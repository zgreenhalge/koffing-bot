import asyncio

from features.onmessage.OnMessageFeature import OnMessageFeature
from util.Logging import get_logger
from util.Messaging import respond, get_mentioned
from util.Role import get_role, members_of_role
from util.Settings import cmd_prefix, enabled, SILENT_MODE, skronk_timeout, settings, skronks
from util.Task import create_task
from util.User import privileged, get_discriminating_name

logger = get_logger()
SKRONKED = "SKRONK'D"
skronk_times = {}


def get_skronk_role(guild):
	return get_role(guild, SKRONKED)


def get_skronk_time(member_id):
	"""
	Gets the time left for a user specific id and returns it in minutes
	"""
	id_str = str(member_id)
	if id_str not in skronk_times:
		return -1
	return int(int(skronk_times[id_str]) / 60)


def is_skronked(member, skronk_role):
	"""
	Returns true if the member is skronked in this guild
	"""
	if skronk_role is None:
		return False

	for role in member.roles:
		if role == skronk_role:
			return True
	return False


class Skronk(OnMessageFeature):
	"""
	Does all the skronking
	"""

	def __init__(self, client):
		super().__init__(client)
		self.command_str = "skronk"

	async def execute(self, *args):
		message = args[0]

		content = message.content.replace(cmd_prefix + 'skronk', '', 1).lstrip().rstrip()
		if not enabled['skronk']:
			self.logger.info('Skronking is not enabled -- not responding')
		elif content.startswith('timeout'):
			if not privileged(message.author):
				if not SILENT_MODE:
					await respond(message, "I'm afraid you can't do that {}".format(message. author.mention), emote="x")
				return
			content = content.replace('timeout', '', 1).lstrip().rstrip()
			if content.isdigit():
				old = skronk_timeout()
				settings['skronk_timeout'] = content
				await respond(message, 'Skronk timeout changed from {}s to {}s'.format(old, content))
			else:
				await respond(message, 'Please give a valid timeout in seconds', emote="x")
		elif content.startswith('clear') and privileged(message.author):
			content = content.replace('clear', '', 1).lstrip().rstrip()
			await self.clear_skronks(message, force=content.startswith('force'), user_clear=True)
		else:
			await self.skronk(message)

	async def clear_skronks(self, message, force=False, user_clear=False):
		"""
		Clears all skronks. If this is not a forced clear, it will not happen if the author is skronked
		"""
		self.logger.info('Attempting to clear all skronks...')

		if not privileged(message.author):
			await respond(message, "I'm afraid you can't do that {}".format(message.author.mention), emote="x")
			return

		skronk_role = get_skronk_role(message.guild)
		if skronk_role in message.author.roles and not force:
			await respond(message, "You can't do that..", emote="x")
			if not SILENT_MODE:
				await respond(message, cmd_prefix + "skronk {}".format(message.author.mention))
			return

		tagged = get_mentioned(message)
		skronked = members_of_role(message.guild, skronk_role)
		names = ""
		if len(tagged) > 0:
			for member in tagged:
				if skronk_role in member.roles:
					await self.remove_skronk(member, message, silent=True, wait=False, absolute=force, user_clear=True)
					names += member.mention + ", "
		else:
			for member in skronked:
				await self.remove_skronk(member, message, silent=True, wait=False, absolute=force, user_clear=True)
				names += member.mention + ", "
		names = names.rstrip(', ')

		if len(names) > 0:
			await respond(message, "Hey {}... Your skronkin' lil ass was just saved by {}!".format(names, message.author.mention))
		else:
			await respond(message, "There was no one to remove from skronk...", emote="x")

	async def remove_skronk(self, member, message, silent=False, wait=True, absolute=False, user_clear=False):
		"""
		Removes @member from skronk
		"""
		global skronk_times
		if wait:
			await asyncio.sleep(int(skronk_timeout()))

		discriminating_name = get_discriminating_name(member)
		self.logger.info('Attempting to deskronk {}'.format(discriminating_name))

		if str(member.id) in skronk_times:
			skronk_times[str(member.id)] = int(skronk_times[str(member.id)]) - int(skronk_timeout())
			if int(skronk_times[str(member.id)]) == 0 or absolute or user_clear:
				del skronk_times[str(member.id)]
			else:
				self.logger.info('Skronk has not yet expired!')
				await respond(message, "Only {}m of shame left {}".format(str(get_skronk_time(member.id)), member.mention))
				await self.remove_skronk(member, message, silent, wait, absolute)
				return

		skronk_role = get_skronk_role(message.guild)
		if skronk_role is not None and skronk_role in member.roles:
			await member.remove_roles(skronk_role)
			self.logger.info(' Deskronked {}'.format(discriminating_name))
			if not silent:
				await respond(message, "You're out of skronk {}!".format(member.mention))
		else:
			self.logger.warning(' Unable to deskronk {}; looked for {} in {}.'.format(discriminating_name, skronk_role, member.roles))

	async def skronk(self, message):
		"""
		Skronks @member
		"""
		self.logger.info('Skronking..')

		global skronk_times
		skronk_role = get_skronk_role(message.guild)
		if skronk_role is None:
			await respond(message, "There will be no skronking here.", emote="x")
			return

		skronked = get_mentioned(message)
		if len(skronked) == 0:
			await respond(message, "Tag someone to skronk them!", emote="x")
			return

		# Is the author skronked already?
		if is_skronked(message.author, self.skronk):
			await respond(message, "What is skronked may never skronk.", emote="x")
			return

		no_skronk = []
		skronk_em = False
		for member in skronked:
			# Is the author trying to skronk himself?
			if member == message.author:
				await respond(message,
							  "You can't skronk yourself {}... let me help you with that.".format(
								  message.author.mention),
							  True)
				skronk_em = True
				no_skronk.append(member)
				continue

			# Are they trying to skronk the skronker???
			if member.id == self.client.user.id:
				await respond(message, "You tryna skronk me??", True)
				skronk_em = True
				no_skronk.append(member)
				continue

		# Clean up list of skronkees
		for member in no_skronk:
			if member in skronked:
				skronked.remove(member)

		if skronk_em:
			await respond(message, cmd_prefix + "skronk {}".format(message.author.mention), True)
		# Okay, let's do the actual skronking
		for member in skronked:
			if member.id in skronks:
				# if they've been skronked already, extend it ?
				skronks[str(member.id)] += 1
			else:
				# the base case, 1 skronk where none was
				skronks[str(member.id)] = 1
			if str(member.id) in skronk_times:
				# add up the time for our skronk
				skronk_times[str(member.id)] = int(skronk_times[str(member.id)]) + int(skronk_timeout())
			else:
				skronk_times[str(member.id)] = int(skronk_timeout())
				create_task(self.remove_skronk(member, message))  # Spin off a separate task to wait before removing skronks
			await member.add_roles(skronk_role)
			await respond(message, "{} got SKRONK'D!!!! ({}m left)".format(member.mention, str(get_skronk_time(member.id))))
