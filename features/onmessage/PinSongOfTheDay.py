from discord import Forbidden, NotFound

from features.onmessage.OnMessageFeature import OnMessageFeature
from util.Messaging import koffing_reaction
from util.Settings import enabled


class PinSongOfTheDay(OnMessageFeature):

	def should_execute(self, message):
		return message.content.startswith('#sotd') and enabled['sotd_pin']

	async def execute(self, *args):
		self.logger.info('Pinning #SotD')
		await self.pin(args[0])

	async def pin(self, message):
		"""
		Pins a message
		"""
		self.logger.info('Pinning message')
		try:
			await koffing_reaction(message)
			await self.client.pin_message(message)
		except NotFound:
			self.logger.warning('Message or channel has been deleted, pin failed')
		except Forbidden:
			self.logger.warning('Koffing-bot does not have sufficient permissions to pin in %s::%s',
						   message.guild.name, message.channel.id)
		except Exception as e:
			self.logger.error('Could not pin message: {}'.format(e))
