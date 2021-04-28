from features.onmessage.OnMessageFeature import OnMessageFeature
from util.Messaging import respond
from util.Settings import cmd_prefix


class HypeEcho(OnMessageFeature):
	"""
	Beefs up the message and parrots it back
	"""

	def __init__(self, client):
		super().__init__(client)
		self.command_str = "hype"

	async def execute(self, *args):
		self.logger.info('Hyping message!')
		message = args[0]

		phrase = message.content.replace('{}hype'.format(cmd_prefix), '', 1).lstrip().rstrip()

		if phrase == "":
			await respond(message, "Skronk!", emote="x")
			return

		hyped = "***{}***  boyooooooo".format(" ".join(phrase).upper())
		await respond(message, hyped, True)
