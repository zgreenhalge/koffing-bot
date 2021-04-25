import discord

from features.onmessage.OnMessageFeature import OnMessageFeature
from util import Settings, FeatureUtils
from util.ChannelUtils import mute, muted, unmute
from util.ClientUtils import ask_exit, ask_restart
from util.FeatureUtils import reload_features
from util.LoggingUtils import get_logger
from util.MessagingUtils import generate_koffing, shutdown_message, respond
from util.UserUtils import privileged, get_discriminating_name

HELP = ('Koffing~~ I will listen to any trainer with enough badges!```'
		'\nCommands (*=requires privilege):'
		'\n /koffing help'
		'\n*/koffing mute'
		'\n*/koffing unmute'
		'\n*/koffing admin [list] [remove (@user) [@user]] [add (@user) [@user]]'
		'\n*/koffing play [name]'
		'\n*/koffing return```'
		)


class AdminConsole(OnMessageFeature):

	__instance = None

	def __init__(self, client):
		super().__init__(client)
		self.logger = get_logger()
		AdminConsole.__instance = self

	@staticmethod
	def get_instance(client):
		if AdminConsole.__instance is None:
			AdminConsole(client)
		return AdminConsole.__instance

	@staticmethod
	def clear_instance():
		AdminConsole.__instance = None

	def should_execute(self, message):
		run = message.content.startswith(Settings.cmd_prefix + 'koffing ')
		return run

	async def execute(self, *args):
		if args is None or len(args) == 0:
			self.logger.warning("No arguments passed!")
			return

		await self.process(args[0])

# Implementation below ------------------------------------------------------------

	def get_admin_list(self, guild):
		"""
		Gets a string containing the list of bot admins
		"""
		self.logger.info('Obtaining admin list')
		admin_str = 'listens to the following trainers:\n'
		for user in Settings.admin_users:
			admin = guild.get_member_named(user)
			if admin is not None:
				admin_str += ' -' + admin.mention + '\n'
		return admin_str

	async def remove_admin(self, message):
		"""
		Remove the mentioned members from the bot admin list
		"""
		users = message.mentions
		for user in users:
			user_str = get_discriminating_name(user)
			if user_str in Settings.admin_users:
				msg_str = 'Removed {} from the admin list.'.format(user.mention)
				self.logger.info('' + msg_str)
				Settings.admin_users.remove(user_str)
				await respond(message, msg_str)
		self.logger.info('Done removing admins.')

	async def add_admin(self, message):
		"""
		Add the mentioned members to the bot admin list
		"""
		users = message.mentions

		for user in users:
			user_str = get_discriminating_name(user)
			if user_str not in Settings.admin_users:
				msg_str = 'Added {} to the admin list.'.format(user.mention)
				self.logger.info('' + msg_str)
				Settings.admin_users.append(user_str)
				await respond(message, msg_str)
		self.logger.info('Done adding admins.')

	async def process(self, message):
		"""
		-Koffing admin and config options
		-Help
		-Admin management
		-Mute channels
		-Change game displayed
		-Manually save state
		-Shut down bot
		"""
		# First, strip out any prefixes used to trigger the command
		# Normally, we expect it to start with '!koffing'
		# But admin console has s special DM shortcut, so prefix could be just '!' as well
		content = message.content
		if content.startswith(Settings.cmd_prefix + 'koffing'):
			content = content.replace(Settings.cmd_prefix + 'koffing', '', 1).lstrip().rstrip()
		elif content.startswith(Settings.cmd_prefix):
			content = content.replace(Settings.cmd_prefix, '', 1).lstrip().rstrip()

		self.logger.debug("Entered admin console for command {}".format(content))

		guild = message.guild
		channel = message.channel
		author = message.author

		if content.startswith('help'):
			await respond(message, HELP)

		if not privileged(author):
			await respond(message, "I'm afraid you can't do that {}".format(author.mention),
										 emote="x")
			return

		# Admin management
		elif content.startswith('admin'):
			content = content.replace('admin', '', 1).lstrip().rstrip()
			if content.startswith('list'):
				await respond(message, self.get_admin_list(guild), ignore_silent=True)
			elif content.startswith('rm') or content.startswith('remove'):
				await self.remove_admin(message)
			elif content.startswith('add'):
				await self.add_admin(message)

		# Mute control (channel based). Stops koffing from listening and MessagingUtils.responding to channels on the list
		elif content.startswith('mute'):
			if not Settings.enabled["mute"]:
				await respond(message, 'Mute is not enabled', emote="x")
			else:
				await respond(message, "Koffing...")
				mute(guild, channel)

		# Unmute control. Gets koffing to listen to a channel again
		elif content.startswith('unmute'):
			if not Settings.enabled["mute"]:
				await respond(message, 'Mute is not enabled', emote="x")
			else:
				if muted(guild, channel):
					response, emoji = generate_koffing(guild)
					self.logger.info('MessagingUtils.responding to "%s" (%s) in %s::%s', author.display_name,
									 get_discriminating_name(author),
									 guild.name, channel.id)
					await respond(message, response)
				unmute(guild, channel)

		# Game display
		elif content.startswith('game') or content.startswith('play'):
			if not Settings.enabled["game"]:
				await respond(message, 'Game is not enabled', emote="x")
			else:
				Settings.game_str = message.content[13:].lstrip().rstrip()
				self.logger.info("Setting bot to playing '{}'".format(Settings.game_str))
				await self.client.change_presence(game=discord.Game(name=Settings.game_str))

		# Manual save
		elif content.startswith('save'):
			Settings.save_all()
			await respond(message, "State saved.")

		# Reload listed tasks & load settings from disk
		elif content.startswith('reload'):
			Settings.load_settings()
			reload_features()
			self.logger.info("Reload complete!")
			await respond(message, "Reload successful.")

		# Silent mode toggle
		elif content.startswith('quiet'):
			Settings.SILENT_MODE = not Settings.SILENT_MODE
			self.logger.info("Toggling silent mode to {}".format(Settings.SILENT_MODE))
			response, emoji = generate_koffing(message.guild)
			await respond(message, response)

		# Kill bot
		elif content.startswith('return') or content.startswith('shutdown'):
			Settings.save_all()
			await shutdown_message(self.client, message)
			ask_exit(self.client)

		elif content.startswith('restart'):
			Settings.save_all()
			await shutdown_message(self.client, message)
			ask_restart(self.client)

		elif content.startswith('stop'):
			for task in FeatureUtils.bkg_features:
				await task.serialize()
				if not task.stopping:
					task.stopping = True

		# Unrecognized command
		else:
			self.logger.info('Unknown command attempt from %s: [%s]', get_discriminating_name(author),
							 (message.content + '.')[:-1].lower())
			await respond(message, "Skronk!", emote="x")
