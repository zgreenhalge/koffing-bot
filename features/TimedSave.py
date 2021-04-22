import asyncio

from features.BackgroundFeature import BackgroundFeature
from util import Settings


class TimedSave(BackgroundFeature):
	"""
	Every SAVE_TIMEOUT seconds, trigger Settings.save_all()
	Default 3600 second sleep.
	"""

	def __init__(self, client):
		super().__init__(client)

	async def execute(self, *args):
		while not self.stopping:
			await asyncio.sleep(Settings.SAVE_TIMEOUT)  # Sleep first so we don't save as soon as we launch
			Settings.save_all()

		print("Exiting TimedSave loop!")
		super.stopped = True
