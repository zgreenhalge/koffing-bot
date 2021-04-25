from features.background.BackgroundFeature import BackgroundFeature
from util.DateTimeUtils import prettify_seconds
from util.TaskUtils import running_tasks


class TaskCuller(BackgroundFeature):
	"""
	Sleep for `cull_timeout` seconds, then remove any tasks that return `done() == True` from the running task list
	After `noop_limit` consecutive no-ops, the sleep duration is increased. The duration is reset to the default when a cull occurs.
	"""
	cull_timeout = sleep_time = 15
	noop_limit = 3
	noop_count = 0
	was_noop = False

	def __init__(self, client):
		super().__init__(client, self.cull_timeout)

	async def process(self, *args):
		complete = []
		for task in running_tasks:
			if task.done():
				self.logger.debug("{} completed successfully, removing from list.".format(task.get_name()))
				complete.append(task)
			else:
				self.logger.debug("{} still running.".format(task.get_name()))

		for task in complete:
			running_tasks.remove(task)

		num_culled = len(complete)
		if num_culled == 0:
			self.noop_count += 1
			self.was_noop = True
		else:
			self.noop_count = 0
			self.was_noop = False

		self.logger.debug("{} culled. {} running.".format(num_culled, len(running_tasks)))

		if self.noop_count % self.noop_limit == 0 and self.was_noop:
			self.sleep_time = self.sleep_time * self.noop_limit
			self.logger.info("{} consecutive no-ops. Sleep increased to {}s".format(self.noop_count, prettify_seconds(self.sleep_time)))

	def configuration(self):
		self.logger.info("Timeout: {}s | Consecutive no-op backoff: {}".format(prettify_seconds(self.cull_timeout), self.noop_limit))
