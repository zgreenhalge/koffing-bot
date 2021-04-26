from features.background.BackgroundFeature import BackgroundFeature
from features.background.TaskCuller import TaskCuller
from util import Settings
from util.DateTimeUtils import prettify_seconds


class TimedSave(BackgroundFeature):
	"""
	Regularly trigger Settings.save_all()
	Default 3600 second (1hr) interval.
	Backs off in tandem with TaskCuller, using background tasks as an indication of activity
	"""

	def __init__(self, client):
		super().__init__(client, Settings.SAVE_TIMEOUT)

	async def process(self, *args):
		Settings.save_all()

		culler = TaskCuller.get_instance(self.client)
		if culler.has_backed_down():
			self.sleep_timeout = self.sleep_timeout * culler.backdown_scale()
			self.logger.info("No activity detected. Sleep increased to {}".format(prettify_seconds(self.sleep_timeout)))
		else:
			self.sleep_timeout = Settings.SAVE_TIMEOUT
			self.logger("Sleep reset to {} ".format(prettify_seconds(self.sleep_timeout)))

	def shutdown(self):
		self.logger.debug("Stopping: {} Stopped: {}".format(self.stopping, self.stopped))

	def configuration(self):
		self.logger.info("Save interval: {} | Sleep interval: {}".format(
																		prettify_seconds(Settings.SAVE_TIMEOUT),
																		prettify_seconds(self.sleep_timeout)))
