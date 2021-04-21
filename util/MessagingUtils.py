import discord

from util import ChannelUtils
from util.LoggingUtils import info
from util.UserUtils import get_discriminating_name

SILENT_MODE = False


async def negative_reaction(message):
	"""
	React negatively to the message
	"""
	emoji = get_x_emoji(message.guild)
	if emoji is None or emoji == '':
		info('Got a blank value for X emote, no reaction possible')
	else:
		info('Reacting with a negative emoji')
		await message.add_reaction(emoji)


async def positive_reaction(message):
	"""
	React positively to the message
	"""
	emoji = get_ok_emoji(message.guild)
	if emoji is None or emoji == '':
		info('Got a blank value for ok_hand emote, no reaction possible')
	else:
		info('Reacting with a positive emoji')
		await message.add_reaction(emoji)


async def koffing_reaction(message):
	"""
	React koffing-ly to the message
	"""
	emoji = get_koffing_emoji(message.guild)
	if emoji is None or emoji == '':
		info('Got a blank value for koffing emote, no reaction possible')
	else:
		info('Reacting with a koffing emoji')
		await message.add_reaction(emoji)


def get_koffing_emoji(guild):
	"""
	Returns the koffing emoji if this guild has one, None otherwise
	"""
	return_emoji = ''
	if guild is None:
		info('No guild information to find koffing!')
		return return_emoji

	for emoji in guild.emojis:
		if emoji.name == 'koffing':
			return_emoji = emoji

	if return_emoji == '':
		info('Could not find koffing emote')
	return return_emoji


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
	if SILENT_MODE and not ignore_silent:
		info('Muted response to "%s" (%s) in %s::%s',
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
		if not ChannelUtils.muted(message.guild, message.channel):
			info('Responding to "%s" (%s) in %s::%s', message.author.display_name,
						get_discriminating_name(message.author), message.guild.name, message.channel.id)
			if SILENT_MODE:
				info('Loud response requested!')
			await message.channel.send(text)


async def direct_response(message, text):
	"""
	Reply directly to a user
	"""
	channel = message.author.dm_channel
	if channel is None:
		await message.author.create_dm()
		channel = message.author.dm_channel

	info('Sending DM to %s', get_discriminating_name(message.author))
	if text == '':
		await channel.send(':eyes:')
	# client.send_message(message.author, ':eyes:')
	else:
		await channel.send(text)
	# client.send_message(message.author, text)
	return