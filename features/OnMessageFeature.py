from features.AbstractFeature import AbstractFeature


class OnMessageFeature(AbstractFeature):

	def should_execute(self, message):
		"""
		Whether or not this feature should execute, based on the given message
		"""
		return False  # Default return value
