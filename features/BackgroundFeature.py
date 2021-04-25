from asyncio import CancelledError

from features.AbstractFeature import AbstractFeature


DEFAULT_SLEEP = 60


class BackgroundFeature(AbstractFeature):

	stopping = False
	stopped = False

	def __init__(self, client):
		super().__init__(client)

	async def process(self, *args):
		"""
		The core routine to be implemented by subclasses
		"""
		return

	def shutdown(self):
		"""
		To be implemented if there is anything to be done when the bot is stopping
		"""
		return

	async def execute(self, *args):
		try:
			await self.process(*args)
		except CancelledError:
			self.stopping = True
			self.shutdown()
			self.stopped = True
