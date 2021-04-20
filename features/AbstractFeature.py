from abc import ABC


class AbstractFeature(ABC):
	"""
	Abstract class representing the basic building blocks of a feature of koffing bot.
	"""

	def __init__(self, outer_client):
		global client
		client = outer_client

	def execute(self, message):
		"""
		Execute this feature against the given message
		"""