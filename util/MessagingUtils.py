import asyncio
from random import randint

import discord

from util import ChannelUtils, LoggingUtils, Settings
from util.UserUtils import get_discriminating_name

logger = LoggingUtils.get_logger()


async def negative_reaction(message):
	"""
	React negatively to the message
	"""
	emoji = get_x_emoji(message.guild)
	if emoji is None or emoji == '':
		logger.info('Got a blank value for X emote, no reaction possible')
	else:
		logger.info('Reacting with a negative emoji')
		await message.add_reaction(emoji)


async def positive_reaction(message):
	"""
	React positively to the message
	"""
	emoji = get_ok_emoji(message.guild)
	if emoji is None or emoji == '':
		logger.info('Got a blank value for ok_hand emote, no reaction possible')
	else:
		logger.info('Reacting with a positive emoji')
		await message.add_reaction(emoji)


async def koffing_reaction(message):
	"""
	React koffing-ly to the message
	"""
	emoji = get_koffing_emoji(message.guild)
	if emoji is None or emoji == '':
		logger.info('Got a blank value for koffing emote, no reaction possible')
	else:
		logger.info('Reacting with a koffing emoji')
		await message.add_reaction(emoji)


def get_koffing_emoji(guild):
	"""
	Returns the koffing emoji if this guild has one, None otherwise
	"""
	return_emoji = ''
	if guild is None:
		logger.info('No guild information to find koffing!')
		return return_emoji

	for emoji in guild.emojis:
		if emoji.name == 'koffing':
			return_emoji = emoji

	if return_emoji == '':
		logger.info('Could not find koffing emote')
	return return_emoji


def generate_koffing(guild):
	"""
	Returns a string of a happy koffing
	"""
	logger.info('Generating koffing string...')
	koffing_emoji = get_koffing_emoji(guild)

	koffing_core_str = 'K' + randint(1, 2) * 'o' + 'ff' + randint(1, 4) * 'i' + 'ng'
	if randint(1, 3) == 1:
		koffing_core_str = koffing_core_str + randint(1, 3) * '?'
	else:
		koffing_core_str = koffing_core_str + randint(1, 5) * '!'

	if koffing_emoji is not None:
		num_koffs = randint(2, 5)
		koffing_str = str(koffing_emoji)
		response = num_koffs * koffing_str + ' ' + koffing_core_str + ' ' + num_koffs * koffing_str
	else:
		response = koffing_core_str
	return response, koffing_emoji


def get_ok_emoji(guild):
	"""
	Returns the checkmark emoji
	"""
	return '\N{OK Hand Sign}'


def get_x_emoji(guild):
	"""
	Returns the checkmark emoji
	"""
	return '\N{Cross Mark}'


async def respond(message, text, ignore_silent=False, emote="koffing"):
	"""
	Respond to a message from a channel; puts line in logs
	"""

	# Make sure a DM didn't show up here somehow
	if message.channel is None or not isinstance(message.channel, discord.abc.GuildChannel):
		await direct_response(message, text)
		return

	# Mute response if we're running in silent mode and we aren't overriding
	if Settings.SILENT_MODE and not ignore_silent:
		logger.info('Muted response to "%s" (%s) in %s::%s',
					message.author.display_name,
					get_discriminating_name(message.author),
					message.guild.name,
					message.channel.id)
		if emote == "koffing":
			await koffing_reaction(message)
		elif emote == "ok":
			await positive_reaction(message)
		elif emote == "x":
			await negative_reaction(message)
	else:
		# Standard respond
		message.channel.typing()
		if not ChannelUtils.muted(message.guild, message.channel):
			logger.info('Responding to "%s" (%s) in %s::%s', message.author.display_name,
						get_discriminating_name(message.author), message.guild.name, message.channel.id)
			if Settings.SILENT_MODE:
				logger.info('Loud response requested!')
			await message.channel.send(text)


async def direct_response(message, text):
	"""
	Reply directly to a user
	"""
	channel = message.author.dm_channel
	if channel is None:
		await message.author.create_dm()
		channel = message.author.dm_channel

	logger.info('Sending DM to %s', get_discriminating_name(message.author))
	if text == '':
		await channel.send(':eyes:')
	# client.send_message(message.author, ':eyes:')
	else:
		await channel.send(text)
	# client.send_message(message.author, text)
	return


async def shutdown_message(client, message):
	"""
	Send a message that the bot is shutting down to
	all channels it can message as well as the one that triggered the shutdown
	"""
	for guild in client.guilds:
		for channel in guild.channels:
			if channel.type == discord.ChannelType.text:
				if ChannelUtils.can_message(guild, channel) and Settings.enabled['greeting']:
					logger.info('Alerting %s::%s to bot shutdown', guild.name, channel.name)
					await channel.send('Koffing-bot is going back to its pokeball~!')
				elif message.guild is None or message.channel is None:
					continue
				elif guild.id == message.guild.id and channel.id == message.channel.id:
					logger.info('Alerting %s::%s to bot shutdown', guild.name, channel.name)
					await channel.send('Koffing-bot is going back to its pokeball~!')


async def delayed_response(message, content, wait_time=300):
	"""
	Sleeps for time seconds and then responds to the message author with the given content
	"""
	await asyncio.sleep(int(float(wait_time)))
	await direct_response(message, content)


def get_mentioned(message, everyone=True):
	"""
	Gets everyone mentioned in a message. Aggregates members from all roles mentioned
	"""
	mentioned = []
	if len(message.mentions) > 0:
		for member in message.mentions:
			mentioned.append(member)

	if len(message.role_mentions) > 0:
		for role in message.role_mentions:
			for member in members_of_role(message.guild, role):
				mentioned.append(member)

	if message.mention_everyone and everyone:
		for member in message.guild.members:
			if member.permissions_in(message.channel).read_messages:
				mentioned.append(member)

	seen = set()
	mentioned = [x for x in mentioned if x not in seen and not seen.add(x)]  # Remove duplicates
	return mentioned
