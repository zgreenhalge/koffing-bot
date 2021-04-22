import asyncio

from features.BackgroundFeature import BackgroundFeature
from util import Settings, LoggingUtils


class TimedSave(BackgroundFeature):
	"""
	Every SAVE_TIMEOUT seconds, trigger Settings.save_all()
	Default 3600 second (1hr) interval.
	Sleeps every 1/60 of the save interval to avoid chewing up processing time while still able to be shutdown quickly
	"""

	def __init__(self, client):
		super().__init__(client)
		self.logger = LoggingUtils.get_logger()

	async def execute(self, *args):

		slept = 0
		sleep_interval = Settings.SAVE_TIMEOUT / 60
		self.logger.info("Loaded TimedSave background feature with {}s save interval, {}s sleep interval".format(Settings.SAVE_TIMEOUT, sleep_interval))

		while not self.stopping:
			# Sleep first so we don't save as soon as we launch
			await asyncio.sleep(sleep_interval)

			# If our accumulated sleep exceeds the save timeout,
			# trigger a save and reset our accumulated sleep time
			slept += sleep_interval
			self.logger.info("Woke up with {}s slept so far ({})".format(slept, slept / Settings.SAVE_TIMEOUT))
			if slept / Settings.SAVE_TIMEOUT > 1:
				Settings.save_all()
				slept = 0

		self.logger.info("Exiting TimedSave loop!")
		self.stopped = True
