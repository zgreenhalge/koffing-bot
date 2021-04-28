from util.LoggingUtils import get_logger

logger = get_logger()


def members_of_role(guild, role):
	"""
	Returns an array of all members for the given role in the given guild
	"""
	logger.info("Looking for all members of {}".format(role.name))
	ret = []
	for member in guild.members:
		if role in member.roles:
			ret.append(member)
	logger.info('Found {} members with the role: {}'.format(len(ret), ret))
	return ret


def get_role(guild, role_name):
	"""
	Finds the role named SKRONK'D
	"""
	logger.info("Looking for skronk role...")
	for role in guild.roles:
		if role.name.lower() == role_name.lower():
			return role
	logger.info("Did not find role named {}".format(role_name))
	return None