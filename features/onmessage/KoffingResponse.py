from features.onmessage.OnMessageFeature import OnMessageFeature
from util.ChannelUtils import can_message
from util.MessagingUtils import generate_koffing, respond
from util.Settings import enabled, SILENT_MODE


class KoffingResponse(OnMessageFeature):
	"""
	Checks a message content for the word 'koffing' and gets excited if its there
	"""

	def should_execute(self, message):
		return not message.author.id == self.client.user.id and 'koffing' in message.content.lower()

	async def execute(self, *args):
		self.logger.debug('Found a koffing in the message!')
		message = args[0]

		if can_message(message.guild, message.channel) and enabled["text_response"]:
			response, emoji = generate_koffing(message.guild)

			await respond(message, response)
			if emoji is not None and not SILENT_MODE:
				await message.add_reaction(emoji)
