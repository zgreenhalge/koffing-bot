import asyncio
from asyncio import CancelledError

from features.AbstractFeature import AbstractFeature


DEFAULT_SLEEP = 60


class BackgroundFeature(AbstractFeature):
	"""
	An abstract feature that runs in the background.
	While stopping = False, will sleep for the configured timeout and then execute process()
	"""

	stopping = False
	stopped = False

	def __init__(self, client, sleep_timeout=60):
		super().__init__(client)
		self.sleep_timeout = sleep_timeout
		self.configuration()

	async def process(self, *args):
		"""
		To be implemented
		The core routine executed once per sleep cycle
		"""

	def shutdown(self):
		"""
		To be implemented , if desired
		Executed when cancel is called on the task
		"""

	def configuration(self):
		"""
		To be implemented, if desired
		Print out the configuration of the background task
		"""

	async def execute(self, *args):
		"""
		While this Task.stopping is False, sleep for sleep_timeout seconds then invoke process().
		When a CancelledError is caught, invoke shutdown() to allow for graceful shutdown.
		"""
		try:
			while not self.stopping:
				await asyncio.sleep(self.sleep_timeout)
				await self.process(*args)
		except CancelledError:
			self.stopping = True
			self.shutdown()
			self.stopped = True
