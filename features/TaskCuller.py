import asyncio

from features.BackgroundFeature import BackgroundFeature
from util.DateTimeUtils import prettify_seconds
from util.TaskUtils import running_tasks


class TaskCuller(BackgroundFeature):

	cull_timeout = 15
	noop_limit = 3

	async def process(self, *args):
		"""
		Sleep for cull_timeout seconds, then remove any tasks that return done() == True from the running task list
		After 5 consecutive no-ops, the sleep duration is multiplied by the default. The duration is reset to the default when we cull tasks.
		"""
		noop_count = 0
		sleep_time = self.cull_timeout
		was_noop = False
		self.logger.info("Timeout: {}s | Consecutive no-op backoff: {}".format(prettify_seconds(self.cull_timeout), self.noop_limit))

		while not self.stopping:

			if noop_count % self.noop_limit == 0 and was_noop:
				sleep_time = sleep_time * self.cull_timeout
				self.logger.info("{} consecutive no-ops. Sleep increased to {}s".format(noop_count, prettify_seconds(sleep_time)))
			await asyncio.sleep(sleep_time)

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
				noop_count += 1
				was_noop = True
			else:
				noop_count = 0
				was_noop = False

			self.logger.debug("{} culled. {} running.".format(num_culled, len(running_tasks)))
