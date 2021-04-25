from features.background.BackgroundFeature import BackgroundFeature
from util import Settings
from util.DateTimeUtils import prettify_seconds


class TimedSave(BackgroundFeature):
	"""
	Every SAVE_TIMEOUT seconds, trigger Settings.save_all()
	Every 1/60 of the save interval check if we should shut down.
	Default 3600 second (1hr) interval.
	"""
	slept = 0

	def __init__(self, client):
		super().__init__(client, Settings.SAVE_TIMEOUT/60)

	async def process(self, *args):
		self.slept += self.sleep_timeout
		ratio = self.slept / Settings.SAVE_TIMEOUT

		# Report in every 1/4 of interval
		if ratio % 0.25 == 0:
			self.logger.debug("Slept {} so far - {}%".format(prettify_seconds(self.slept), ratio*100))

		# If our accumulated sleep exceeds the save timeout,
		# trigger a save and reset our accumulated sleep time
		if ratio >= 1:
			Settings.save_all()
			self.slept = 0

	def shutdown(self):
		self.logger.debug("Stopping: {} Stopped: {}".format(self.stopping, self.stopped))

	def configuration(self):
		self.logger.info("Save interval: {}s | Sleep interval: {}s".format(
																		prettify_seconds(Settings.SAVE_TIMEOUT),
																		prettify_seconds(self.sleep_timeout)))
