from features.AbstractFeature import AbstractFeature
from util.Settings import cmd_prefix


class OnMessageFeature(AbstractFeature):

	command_str = None

	def should_execute(self, message):
		"""
		Whether or not this feature should execute, based on the given message
		"""
		if self.command_str is not None:
			return message.content.startswith("{}{}".format(cmd_prefix, self.command_str))
		else:
			return False
