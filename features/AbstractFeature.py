from abc import ABC

from util import Logging


class AbstractFeature(ABC):
	"""
	Abstract class representing the basic building blocks of a feature of koffing bot.
	"""

	def __init__(self, outer_client):
		self.client = outer_client
		self.logger = Logging.get_logger()

	async def execute(self, *args):
		"""
		Execute this feature
		"""

	async def serialize(self):
		"""
		Write any pending tasks to disk
		"""

	async def deserialize(self):
		"""
		Read any leftover tasks from disk and restart processing
		"""