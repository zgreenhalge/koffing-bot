from features.background.BackgroundFeature import BackgroundFeature
from util.DateTime import prettify_seconds
from util.Task import running_tasks


class TaskCuller(BackgroundFeature):
	"""
	Sleep for `cull_timeout` seconds, then remove any tasks that return `done() == True` from the running task list
	After `noop_limit` consecutive no-ops, the sleep duration is increased. The duration is reset to the default when a cull occurs.
	"""
	cull_timeout = 30
	noop_limit = 5
	noop_count = 0
	was_noop = False
	__instance = None

	def __init__(self, client):
		super().__init__(client, self.cull_timeout)
		TaskCuller.__instance = self

	@staticmethod
	def get_instance(client):
		if TaskCuller.__instance is None:
			TaskCuller(client)
		return TaskCuller.__instance

	@staticmethod
	def clear_instance():
		TaskCuller.__instance = None

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
			if self.sleep_timeout != self.cull_timeout:
				self.sleep_timeout = self.cull_timeout
				self.logger.info("Sleep reset to {} ".format(prettify_seconds(self.sleep_timeout)))

		self.logger.debug("{} culled. {} running.".format(num_culled, len(running_tasks)))

		if self.should_backdown() and self.was_noop:
			self.sleep_timeout = self.sleep_timeout * self.noop_limit
			self.logger.info("{} consecutive no-ops. Sleep increased to {}".format(self.noop_count, prettify_seconds(self.sleep_timeout)))

	def configuration(self):
		return "Timeout: {} | Consecutive no-op backoff: {}".format(prettify_seconds(self.cull_timeout), self.noop_limit)

	def backdown_scale(self):
		ret = self.noop_count / self.noop_limit
		self.logger.debug("Scale: {}".format(ret))
		return ret

	def should_backdown(self):
		return self.noop_count % self.noop_limit == 0

	def has_backed_down(self):
		return self.noop_count >= self.noop_limit
