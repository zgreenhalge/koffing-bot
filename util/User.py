from util import Settings, Logging

logger = Logging.get_logger()


def get_discriminating_name(user):
	"""
	Returns a string of the form <Username>#<USERDISCRIMINATOR>
	"""
	return '{}#{}'.format(user.name, user.discriminator)


def privileged(user):
	"""
	True if this user is a bot admin, False otherwise
	"""
	name = get_discriminating_name(user)
	if name in Settings.admin_users:
		return True
	else:
		logger.info('%s is not in the bot admin list', name)
		return False


def get_preferred_name(user):
	"""
	Gets either a user's nickname or their name, if there is no nickname
	"""
	if user.nick is not None:
		return user.nick
	else:
		return user.name


def get_pretty_name(user):
	"""
	Gets a pretty string of a user's name and nickname or just name, if there is no nickname
	"""
	if user.nick is not None:
		return user.name + ' (' + user.nick + ')'
	else:
		return user.name
