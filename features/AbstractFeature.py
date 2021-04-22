from abc import ABC


class AbstractFeature(ABC):
	"""
	Abstract class representing the basic building blocks of a feature of koffing bot.
	"""

	def __init__(self, outer_client):
		self.client = outer_client

	async def execute(self, *args):
		"""
		Execute this feature
		"""

	def serialize(self):
		"""
		Write any pending tasks to disk
		"""

	def deserialize(self):
		"""
		Read any leftover tasks from disk and restart processing
		"""