from util import Settings, LoggingUtils

logger = LoggingUtils.get_std_logger()


def can_message(guild, channel):
	"""
	True if the bot is authorized and unmuted for the channel, False otherwise
	"""
	return authorized(guild, channel) and not muted(guild, channel)


def authorized(guild, channel):
	"""
	True if the bot is authorized in this channel
	"""
	if str(guild.id) in Settings.authorized_guilds:
		if str(channel.id) in Settings.authorized_channels[str(guild.id)]:
			return True
		else:
			# logger.info('%s is not an authorized channel in %s', channel.id, guild.id)
			pass
	else:
		# logger.info('%s is not an authorized guild id', guild.id)
		pass
	return False


def muted(guild, channel):
	"""
	True if the bot is muted in this channel
	"""
	if str(guild.id) in Settings.muted_channels:
		return str(channel.id) in Settings.muted_channels[str(guild.id)]
	return False


def mute(guild, channel):
	"""
	Adds the channel to the muted list
	"""
	logger.info('Muting channel {}::{}...', guild.name, channel.name)
	if str(guild.id) in Settings.muted_channels:
		if str(channel.id) not in Settings.muted_channels[str(guild.id)]:
			Settings.muted_channels[str(guild.id)].append(str(channel.id))
	else:
		Settings.muted_channels[str(guild.id)] = [str(channel.id)]


def unmute(guild, channel):
	"""
	Removes the channel from the muted list
	"""
	logger.info('Unmuting channel {}::{}...', guild.name, channel.name)
	if str(guild.id) in Settings.muted_channels:
		if str(channel.id) in Settings.muted_channels[str(guild.id)]:
			Settings.muted_channels[str(guild.id)].remove(str(channel.id))
