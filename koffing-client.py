import asyncio
import logging
import os
import sys
from datetime import datetime
from datetime import timedelta
from random import randint

import discord
import pytz
from discord import NotFound, Forbidden

import util
from util import Settings
from util.FileUtils import *
from util.MessagingUtils import *
from util.UserUtils import *

print("Welcome inside koffing's head")

if len(sys.argv) < 2:
	TOKEN = input('Please enter token: ')
else:
	TOKEN = sys.argv[1].lstrip().rstrip()

START_MESSAGES = ["Koffing-bot, go~!", "Get 'em Koffing-bot~!"]
LOG_FORMAT = '[%(asctime)-15s] [%(levelname)+7s] [%(threadName)+10s] [%(thread)d] [%(module)s.%(funcName)s] - %(message)s'
HELP = ('Koffing~~ I will listen to any trainer with enough badges!```'
		'\nCommands (*=requires privilege):'
		'\n /koffing help'
		'\n*/koffing mute'
		'\n*/koffing unmute'
		'\n*/koffing admin [list] [remove (@user) [@user]] [add (@user) [@user]]'
		'\n*/koffing play [name]'
		'\n*/koffing return```'
		)

SKRONKED = "SKRONK'D"
CONFIG_FILE_NAME = 'koffing.cfg'
FEATURE_FILE_NAME = "feature_toggle.cfg"
VOTE_FILE_NAME = 'vote_count.txt'
SKRONK_FILE_NAME = 'skronk.txt'

CONFIG_FILE_PATH = os.path.join(os.path.dirname(__file__), 'config', CONFIG_FILE_NAME)
FEATURE_FILE_PATH = os.path.join(os.path.dirname(__file__), 'config', FEATURE_FILE_NAME)
VOTE_FILE_PATH = os.path.join(os.path.dirname(__file__), 'config', VOTE_FILE_NAME)
SKRONK_FILE_PATH = os.path.join(os.path.dirname(__file__), 'config', SKRONK_FILE_NAME)

koffings = dict()
oks = dict()
dev = True
date_format = '%Y-%m-%d'
pretty_date_format = '%a %b %Y %I:%M:%S %p'
cmd_prefix = '!'
est_tz = pytz.timezone('US/Eastern')
# --------------------------------------------------------------------
# Logging set up
print("Setting up loggers...")


class StreamToLogger(object):
	"""
	Fake stream-like object that redirects writes to a logger instance.
	"""

	def __init__(self, logger, log_level):
		self.logger = logger
		self.log_level = log_level
		self.linebuf = ''

	def write(self, buf):
		if not buf.isspace():
			for line in buf.splitlines():
				if line:
					self.logger.log(self.log_level, line)

	def flush(self):
            return
        # do nothing (:


datetime_str = datetime.now(tz=est_tz).strftime(date_format)

logging.basicConfig(format=LOG_FORMAT, level=logging.INFO)
log_dir = os.path.join(os.path.dirname(__file__), 'logs')

if not os.path.exists(log_dir):
	os.makedirs(log_dir)

logHandler = logging.FileHandler(os.path.join(os.path.dirname(__file__), 'logs', 'LOG_' + datetime_str + '.txt'),
								 mode='a', encoding='utf-8')
logHandler.setLevel(logging.INFO)
logHandler.setFormatter(logging.Formatter(LOG_FORMAT))

logger = logging.getLogger(__name__)
logger.addHandler(logHandler)

util.MessagingUtils.logger = logger

logger.info("Stdout logger intialized")

err_logger = logging.getLogger('STDERR')
errHandler = logging.FileHandler(os.path.join(os.path.dirname(__file__), 'logs', 'ERR_' + datetime_str + '.txt'),
								 mode='a', encoding='utf-8')
errHandler.setFormatter(logging.Formatter(LOG_FORMAT))

err_logger.addHandler(errHandler)

sys.stderr = StreamToLogger(err_logger, logging.ERROR)

err_logger.info('###############################################')
err_logger.info('#-----------------NEW SESSION-----------------#')
err_logger.info('#------------------' + datetime_str + '-----------------#')
err_logger.info('###############################################')
# --------------------------------------------------------------------
# Control lists
logger.info("Loading settings...")

Settings.load_settings()

skronk_times = {}
task_list = []
# --------------------------------------------------------------------
# Finally, the main program!

client = discord.Client(intents=discord.Intents.all())


@client.event
async def on_ready():
	"""
	Called when the client has succesfully started up & logged in with our token
	"""
	logger.info('\n-----------------\nLogged in as %s - %s\n-----------------', client.user.name, client.user.id)
	if dev:
		logger.info('Member of the following guilds:')
		for guild in client.guilds:
			logger.info('  %s (%s)', guild.name, guild.id)

	new_game = discord.Game(Settings.game_str)
	await client.change_presence(activity=new_game)

	for guild in client.guilds:
		if guild.id in Settings.authorized_guilds:
			for channel in guild.channels:
				if channel.type == discord.ChannelType.text and can_message(guild, channel) and Settings.enabled['greeting']:
					logger.info('Alerting %s::%s to bot presence', guild.name, channel.id)
					await client.send_message(channel, START_MESSAGES[randint(0, len(START_MESSAGES) - 1)])
	logger.info('Koffing-bot is up and running!')


@client.event
async def on_message(message):
	"""
	Fires when the client receieves a new message. Main starting point for message & command processing
	"""
	if message.channel is None or message.guild is None or not isinstance(message.channel, discord.abc.GuildChannel):
		await on_direct_message(message)
		return

	logger.info('Received message from "%s" (%s) in %s::%s', get_preferred_name(message.author),
				get_discriminating_name(message.author), message.guild.name, message.channel.name)
	if not authorized(message.guild, message.channel):
		# logger.info('  Channel is unauthorized - not processing')
		return

	global game_str, SILENT_MODE
	guild = message.guild
	channel = message.channel
	content = (message.content + '.')[:-1].lower()
	author = message.author

	# Koffing admin and config options
	if content.startswith(cmd_prefix + 'koffing '):
		content = content.replace(cmd_prefix + 'koffing', '', 1).lstrip().rstrip()
		await admin_console(message, content)

	# Actual commands and features:
	# Auto pin messages starting with #SotD
	# Voting (incl. leaderboards and history)
	# Skronking and skronk management

	# Sotd pinning
	elif content.startswith('#sotd'):
		if not Settings.enabled['sotd_pin']:
			logger.info("sotd_pin is not enabled")
			# Don't alert channel to pin disabled
			return
		logger.info('Pinning #SotD')
		await pin(message)

	# Voting
	elif content.startswith(cmd_prefix + 'vote'):
		if not Settings.enabled['voting']:
			await respond(message, "Voting is not enabled", emote="x")
		else:
			# check vote timeout & reset if needed
			content = content.replace(cmd_prefix + 'vote', '', 1).lstrip().rstrip()
			if content.startswith('leaderboard') or content.startswith('boards') or content.startswith(
					'leaders') or content.startswith('results'):
				await respond(message, get_vote_leaderboards(guild, author), True)
			elif content.startswith('history'):
				await respond(message, get_vote_history(guild, author), True)
			else:
				await place_vote(message)

	# Skronking
	elif content.startswith(cmd_prefix + 'skronk'):
		content = content.replace(cmd_prefix + 'skronk', '', 1).lstrip().rstrip()
		if not Settings.enabled['skronk']:
			logger.info('Skronking is not enabled -- not responding')
		elif content.startswith('timeout'):
			if not privileged(author):
				if not SILENT_MODE:
					await respond(message, "I'm afraid you can't do that {}".format(author.mention), emote="x")
				return
			content = content.replace('timeout', '', 1).lstrip().rstrip()
			if content.isdigit():
				old = skronk_timeout()
				Settings.settings['skronk_timeout'] = content
				await respond(message, 'Skronk timeout changed from {}s to {}s'.format(old, content))
			else:
				await respond(message, 'Please give a valid timeout in seconds', emote="x")
		elif content.startswith('clear') and privileged(author):
			content = content.replace('clear', '', 1).lstrip().rstrip()
			await clear_skronks(message, force=content.startswith('force'), user_clear=True)
		else:
			await skronk(message)

	elif content.startswith(cmd_prefix + 'remindme'):
		await remind_me(message)

	elif content.startswith(cmd_prefix + 'hype'):
		await hype(message)

	# Message content scanning
	else:
		if not message.author.id == client.user.id:
			await check_for_koffing(message)


async def admin_console(message, content):
	"""
	-Koffing admin and config options
	-Help
	-Admin management
	-Mute channels
	-Change game displayed
	-Manually save state
	-Shut down bot
	"""
	global SILENT_MODE, game_str
	guild = message.guild
	channel = message.channel
	author = message.author

	if content.startswith('help'):
		await respond(message, HELP)

	if not privileged(author):
		await respond(message, "I'm afraid you can't do that {}".format(author.mention), emote="x")
		return

	# Admin management
	elif content.startswith('admin'):
		content = content.replace('admin', '', 1).lstrip().rstrip()
		if content.startswith('list'):
			await respond(message, get_admin_list(guild), ignore_silent=True)
		elif content.startswith('rm') or content.startswith('remove'):
			await remove_admin(message)
		elif content.startswith('add'):
			await add_admin(message)

	# Mute control (channel based). Stops koffing from listening and responding to channels on the list
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
				logger.info('Responding to "%s" (%s) in %s::%s', author.display_name, get_discriminating_name(author),
							guild.name, channel.id)
				await respond(message, response)
			unmute(guild, channel)

	# Game display
	elif content.startswith('game') or content.startswith('play'):
		if not Settings.enabled["game"]:
			await respond(message, 'Game is not enabled', emote="x")
		else:
			game_str = message.content[13:].lstrip().rstrip()
			logger.info("Setting bot to playing '{}'".format(game_str))
			await client.change_presence(game=discord.Game(name=game_str))

	# Manual save
	elif content.startswith('save'):
		save_all()
		await respond(message, "State saved.")

	# Load settings from disk
	elif content.startswith('reload'):
		Settings.load_settings()
		await respond(message, "Settings reloaded.")

	# Silent mode toggle
	elif content.startswith('quiet'):
		SILENT_MODE = not SILENT_MODE
		util.MessagingUtils.SILENT_MODE = SILENT_MODE
		response, emoji = generate_koffing(message.guild)
		await respond(message, response)

	# Kill bot
	elif content.startswith('return') or content.startswith('shutdown'):
		save_all()
		await shutdown_message(message)
		ask_exit()

	elif content.startswith('restart'):
		save_all()
		await shutdown_message(message)
		ask_restart()

	# Unrecognized command
	else:
		logger.info('Unknown command attempt from %s: [%s]', get_discriminating_name(author),
					(message.content + '.')[:-1].lower())
		await respond(message, "Skronk!", emote="x")


async def on_direct_message(message):
	"""
	C&C for direct messages, we get forwarded here from on_message()
	"""
	if message.author.id is client.user.id:
		return

	logger.info('Got a DM from %s', get_discriminating_name(message.author))
	content = message.content

	if content.startswith(cmd_prefix + 'remindme'):
		await remind_me(message)
	elif content.startswith(cmd_prefix):
		await admin_console(message, content.replace(cmd_prefix, '', 1))
	else:
		await direct_response(message, '')


async def timed_save():
	"""
	Loops until the bot shuts down, saving state (votes, settings, etc)
	"""
	while not client.is_closed:
		# Sleep first so we don't save as soon as we launch
		await asyncio.sleep(Settings.SAVE_TIMEOUT)
		if not client.is_closed:
			# could have closed between start of loop & sleep
			save_all()


async def shutdown_message(message):
	"""
	Saves state and then alerts all channels that it is shutting down
	"""
	for guild in client.guilds:
		for channel in guild.channels:
			if channel.type == discord.ChannelType.text:
				if can_message(guild, channel) and Settings.enabled['greeting']:
					logger.info('Alerting %s::%s to bot shutdown', guild.name, channel.name)
					await channel.send('Koffing-bot is going back to its pokeball~!')
				elif message.guild is None or message.channel is None:
					continue
				elif guild.id == message.guild.id and channel.id == message.channel.id:
					logger.info('Alerting %s::%s to bot shutdown', guild.name, channel.name)
					await channel.send('Koffing-bot is going back to its pokeball~!')


async def check_for_koffing(message):
	"""
	Checks a message content for the word 'koffing' and gets excited if its there
	"""
	if 'koffing' in message.content.lower() or client.user.mentioned_in(message):
		# logger.info('Found a koffing in the message!')

		if can_message(message.guild, message.channel) and Settings.enabled["text_response"]:
			# Quiet skip this, since that's the point of disabled text response
			if not SILENT_MODE:
				message.channel.typing()

			response, emoji = generate_koffing(message.guild)
			await asyncio.sleep(randint(0, 1))
			await respond(message, response)
			if emoji is not None and not SILENT_MODE:
				await message.add_reaction(emoji)

		# RETURN HERE TO STOP VOICE FROM HAPPENING BEFORE IT WORKS
		return

		# need to figure out ffmpeg before this will work
		if message.author.voice_channel is not None and enabled["voice_response"]:
			logger.info('Attempting to play in voice channel %s', message.author.voice_channel.id)
			voice = voice_client_int(message.guild)
			if voice is None or voice.channel != message.author.voice_channel:
				voice = client.join_voice_channel(message.author.voice_channel)
			player = voice.create_ffmpeg_player('koffing.mp3')
			player.start()


async def remind_me(message):
	"""
	Basic remindme functionality, works for seconds or minutes
	"""
	global est_tz

	logger.info('Generating reminder for %s...', get_discriminating_name(message.author))
	contents = message.content.split(maxsplit=2)
	# ['/remindme', 'time', 'message']
	if len(contents) < 3:
		await respond(message, "Skronk!", emote="x")
		return

	remind_time = contents[1]
	# Check for units on end of string
	if not remind_time.replace(".", "", 1).isdigit():
		if remind_time.endswith('h'):
			remind_time = str(float(remind_time[:-1]) * 3600)
		if remind_time.endswith('m'):
			remind_time = str(float(remind_time[:-1]) * 60)
		elif remind_time.endswith('s'):
			remind_time = str(float(remind_time[:-1]) * 1)
		if not remind_time.replace(".", "", 1).isdigit():
			await respond(message, "Skronk!", emote="x")
			return

	current_time = datetime.now(tz=est_tz)
	wakeup = (current_time + timedelta(seconds=int(float(remind_time)))).strftime(pretty_date_format)

	# Respond based on the length of time to wait
	# TODO - should we even bother with a text response here?
	await respond(message, "Alright, reminding you at {}".format(wakeup))

	if message.guild is not None:
		await koffing_reaction(message)

	task_list.append(client.loop.create_task(delayed_response(message, "This is your reminder from {}:\n\n{}".format(current_time, contents[2]), remind_time)))
	logger.info('Reminder generated for %s in %s seconds (%s)', get_discriminating_name(message.author), remind_time, wakeup)

	return


async def hype(message):
	"""
	Beefs up the message and parrots it back
	"""
	logger.info('Hyping message!')
	phrase = message.content.replace('/hype', '', 1).lstrip().rstrip()
	if phrase == "":
		await respond(message, "Skronk!", emote="x")
		return
	hyped = "***{}***  boyooooooo".format(" ".join(phrase).upper())
	await respond(message, hyped, True)


async def delayed_response(message, content, wait_time=300):
	"""
	Sleeps for time seconds and then responds to the message author with the given content
	"""
	await asyncio.sleep(int(float(wait_time)))
	if not client.is_closed():
		await direct_response(message, content)


async def add_admin(message):
	"""
	Add the mentioned members to the bot admin list
	"""
	users = message.mentions
	channel = message.channel
	for user in users:
		user_str = get_discriminating_name(user)
		if user_str not in Settings.admin_users:
			msg_str = 'Added {} to the admin list.'.format(user.mention)
			logger.info('' + msg_str)
			Settings.admin_users.append(user_str)
			await respond(message, msg_str)
	logger.info('Done adding admins.')


async def remove_admin(message):
	"""
	Remove the mentioned members from the bot admin list
	"""
	users = message.mentions
	channel = message.channel
	for user in users:
		user_str = get_discriminating_name(user)
		if user_str in Settings.admin_users:
			msg_str = 'Removed {} from the admin list.'.format(user.mention)
			logger.info('' + msg_str)
			Settings.admin_users.remove(user_str)
			await respond(message, msg_str)
	logger.info('Done removing admins.')


async def pin(message):
	"""
	Pins a message
	"""
	logger.info('Pinning message')
	try:
		await koffing_reaction(message)
		await client.pin_message(message)
	except NotFound:
		err_logger.warn('Message or channel has been deleted, pin failed')
	except Forbidden:
		err_logger.warn('Koffing-bot does not have sufficient permissions to pin in %s::%s',
						message.guild.name, message.channel.id)
	except Exception as e:
		err_logger.error('Could not pin message: {}'.format(e))


async def place_vote(message):
	"""
	Adds a vote for @member or @role or @everyone
	"""
	global est_tz
	logger.info('Tallying votes...')

	if len(message.mentions) == 0 and len(message.role_mentions) == 0 and not message.mention_everyone:
		await respond(message, "Tag someone to vote for them!", emote="x")
		return

	vote_getters = get_mentioned(message)
	voted_for_self = False
	names = ''
	for member in vote_getters:
		name = get_discriminating_name(member)

		if member.id == message.author.id:
			await respond(message, cmd_prefix + "skronk {} for voting for yourself...".format(message.author.mention),
						  True)
			voted_for_self = True
			continue  # cannot vote for yourself

		names += member.mention + ", "
		cur_votes, start_time = get_current_votes()
		if cur_votes is None:
			cur_votes = {name: 1}
			Settings.votes[date_to_string(datetime.now(tz=est_tz).date())] = cur_votes
		else:
			if name in cur_votes:
				cur_votes[name] = cur_votes[name] + 1
			else:
				cur_votes[name] = 1
			Settings.votes[start_time] = cur_votes

	names = names.rstrip(', ')
	if len(names) > 0:
		await respond(message,
					  'Congratulations {}! You got a vote!{}'.format(names, get_vote_leaderboards(message.guild,
																								  message.author,
																								  False)))
	elif not voted_for_self:
		await respond(message, "You didn't tag anyone you can vote for {}".format(message.author.mention), emote="x")


async def skronk(message):
	"""
	Skronks @member
	"""
	logger.info('Skronking..')

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
	if is_skronked(message.author, message.guild, skronk):
		await respond(message, "What is skronked may never skronk.", emote="x")
		return

	no_skronk = []
	skronk_em = False
	for member in skronked:
		# Is the author trying to skronk himself?
		if member == message.author:
			await respond(message,
						  "You can't skronk yourself {}... let me help you with that.".format(message.author.mention),
						  True)
			skronk_em = True
			no_skronk.append(member)
			continue

		# Are they trying to skronk the skronker???
		if member.id == client.user.id:
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
		if member.id in Settings.skronks:
			# if they've been skronked already, extend it ?
			Settings.skronks[str(member.id)] += 1
		else:
			# the base case, 1 skronk where none was
			Settings.skronks[str(member.id)] = 1
		if str(member.id) in skronk_times:
			# add up the time for our skronk
			skronk_times[str(member.id)] = int(skronk_times[str(member.id)]) + int(skronk_timeout())
		else:
			skronk_times[str(member.id)] = int(skronk_timeout())
			task_list.append(client.loop.create_task(remove_skronk(member, message)))
		await member.add_roles(skronk_role)
		await respond(message, "{} got SKRONK'D!!!! ({}m left)".format(member.mention, str(get_skronk_time(member.id))))


async def remove_skronk(member, message, silent=False, wait=True, absolute=False, user_clear=False):
	"""
	Removes @member from skronk
	"""
	global skronk_times
	if wait:
		await asyncio.sleep(int(skronk_timeout()))

	discriminating_name = get_discriminating_name(member)
	logger.info('Attempting to deskronk {}'.format(discriminating_name))

	if str(member.id) in skronk_times:
		skronk_times[str(member.id)] = int(skronk_times[str(member.id)]) - int(skronk_timeout())
		if int(skronk_times[str(member.id)]) == 0 or absolute or user_clear:
			del skronk_times[str(member.id)]
		else:
			logger.info('Skronk has not yet expired!')
			await respond(message, "Only {}m of shame left {}".format(str(get_skronk_time(member.id)), member.mention))
			task_list.append(client.loop.create_task(remove_skronk(member, message, silent, wait, absolute)))
			return

	skronk_role = get_skronk_role(message.guild)
	if skronk_role is not None and skronk_role in member.roles:
		await member.remove_roles(skronk_role)
		logger.info(' Deskronked {}'.format(discriminating_name))
		if not silent:
			await respond(message, "You're out of skronk {}!".format(member.mention))
	else:
		logger.warning(' Unable to deskronk {}; looked for {} in {}.'.format(discriminating_name, skronk_role, member.roles))


async def clear_skronks(message, force=False, user_clear=False):
	"""
	Clears all skronks. If this is not a forced clear, it will not happen if the author is skronked
	"""
	logger.info('Attempting to clear all skronks...')

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
				await remove_skronk(member, message, silent=True, wait=False, absolute=force, user_clear=True)
				names += member.mention + ", "
	else:
		for member in skronked:
			await remove_skronk(member, message, silent=True, wait=False, absolute=force, user_clear=True)
			names += member.mention + ", "
	names = names.rstrip(', ')

	if len(names) > 0:
		await respond(message,
					  "Hey {}... Your skronkin' lil ass was just saved by {}!".format(names, message.author.mention))
	else:
		await respond(message, "There was no one to remove from skronk...", emote="x")


def get_skronk_time(member_id):
	"""
	Gets the time left for a user specific id and returns it in minutes
	"""
	id_str = str(member_id)
	if id_str not in skronk_times:
		return -1
	return int(int(skronk_times[id_str]) / 60)


def skronk_timeout():
	return int(Settings.settings['skronk_timeout'])


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


def get_skronk_role(guild):
	"""
	Finds the role named SKRONK'D
	"""
	logger.info("Looking for skronk role...")
	for role in guild.roles:
		if role.name.lower() == SKRONKED.lower():
			return role
	logger.info("Did not find role named {}".format(SKRONKED))
	return None


def is_skronked(member, guild, skronk_role):
	"""
	Returns true if the member is skronked in this guild
	"""
	if skronk_role is None:
		return False

	for role in member.roles:
		if role == skronk_role:
			return True
	return False


def get_admin_list(guild):
	"""
	Gets a string containing the list of bot admins
	"""
	logger.info('Obtaining admin list')
	admin_str = 'listens to the following trainers:\n'
	for user in Settings.admin_users:
		admin = guild.get_member_named(user)
		if admin is not None:
			admin_str += ' -' + admin.mention + '\n'
	return admin_str


def get_vote_leaderboards(guild, requester, call_out=True):
	"""
	Returns a string of the current vote leaderboard
	"""
	logger.info('Compiling vote leaderboards...')
	guild_leaders = []
	cur_votes, start = get_current_votes()
	if cur_votes is None:
		return 'No one in {} has recieved any votes!'.format(guild.name)

	for user_name in cur_votes:
		member = guild.get_member_named(user_name)
		if member is not None:
			guild_leaders.append((member, cur_votes[user_name]))

	if len(guild_leaders) == 0:
		return 'No one in {} has recieved any votes!'.format(guild.name)

	sorted_ch_lead = sorted(guild_leaders, key=lambda tup_temp: tup_temp[1], reverse=True)

	leaders = []
	idx = 0
	username = get_discriminating_name(sorted_ch_lead[idx][0])
	score = sorted_ch_lead[idx][1]
	top_score = score

	while score == top_score:
		member = sorted_ch_lead[idx][0]
		if member is not None:
			leaders.append(member)
		idx = idx + 1
		if len(sorted_ch_lead) > idx:
			username = get_discriminating_name(sorted_ch_lead[idx][0])
			score = sorted_ch_lead[idx][1]
		else:
			score = -1

	string = ""
	if len(leaders) > 1:
		for member in leaders:
			string += member.mention + ', '
		string = string.rstrip(', ')
		string = ', and '.join(string.rsplit(', ', 1))
		leader_str = "It's a tie between {}!".format(string)
	else:
		leader_str = "{} is in the lead!".format(leaders[0].mention)

	leaderboard_str = '\n \nLeaderboard for week of {}\n{}```'.format(start, leader_str)
	for tup in sorted_ch_lead:
		leaderboard_str += '{}: {}'.format(get_user_name(tup[0]), tup[1])
		if requester.name == tup[0].name and call_out:
			leaderboard_str += '<-- It\'s you!\n'
		else:
			leaderboard_str += '\n'
	leaderboard_str += '```'
	return leaderboard_str


def get_vote_history(guild, requestor):
	"""
	Returns a string of all the winners of each recorded voting session
	"""
	logger.info('Compiling vote winners...')

	leaders = []
	cur_votes, start = get_current_votes()
	for date in Settings.votes:
		if string_to_date(date) < string_to_date(start) and string_to_date(date) - string_to_date(start) > timedelta(
				-8):
			if len(Settings.votes[date]) > 0:
				sorted_users = sorted(Settings.votes[date], key=lambda tup_temp: tup_temp[1], reverse=False)
				idx = 0
				top_score = Settings.votes[date][sorted_users[idx]]
				username = sorted_users[idx]
				score = Settings.votes[date][username]

				while score == top_score:
					member = guild.get_member_named(username)
					if member is not None:
						leaders.append([date, member, score])
					idx = idx + 1
					if len(sorted_users) > idx:
						username = sorted_users[idx]
						score = Settings.votes[date][username]
					else:
						score = -1

	history_str = 'All-time voting history:```'
	current_date = None

	if len(leaders) == 0:
		history_str = "This guild has no vote winners..."
	else:
		leaders = sorted(leaders, key=lambda tup_temp: datetime.strptime(tup_temp[0], pretty_date_format))
		for tup in leaders:
			if tup[0] != current_date:
				current_date = tup[0]
				history_str += '\n{} - {}: {}'.format(tup[0], get_user_name(tup[1]), tup[2])
			else:
				history_str += '\n             {}: {}'.format(get_user_name(tup[1]), tup[2])
		history_str += '```'

	return history_str


def get_current_votes():
	"""
	Get the votes map for the current session
	"""
	global est_tz
	now = datetime.now(tz=est_tz).date()
	for start in Settings.votes:
		if now - string_to_date(start) < timedelta(7):
			return Settings.votes[start], start
	return None, None


def date_to_string(date):
	"""
	Turn a date object into a string formatted the way we want (YYYY-mm-dd)
	"""
	return date.strftime(pretty_date_format)


def string_to_date(string):
	"""
	Turn a string in YYYY-mm-dd into a date object
	"""
	return datetime.strptime(string, pretty_date_format).date()


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


def get_date():
	"""
	Returns a string of the current date in mm-dd-YYYY
	"""
	global est_tz
	return datetime.now(tz=est_tz).strftime('%m-%d-%Y')


def generate_koffing(guild):
	"""
	Returns a string of a happy koffing
	"""
	logger.info('Generating koffing string...')
	koffing_emoji = get_koffing_emoji(guild)
	koffing_str = None
	response = None

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


def save_all(silent=False):
	"""
	Perform all saves
	"""
	if not silent:
		logger.info('Saving to disk...')
	Settings.save_config(True)
	Settings.save_feature_toggle(True)
	Settings.save_votes(True)
	Settings.save_skronk(True)


def ask_restart():
	"""
	Stop all tasks we have spawned before shutting down with return code 0.
	This signals koffing-ball.py that we should update & restart.
	"""

	logger.info('Stopping tasks...')
	global task_list
	for task in task_list:
		task.cancel()
	asyncio.ensure_future(exit())

	logger.info('Restarting...')
	sys.exit(0)


async def exit():
	"""
	Shutdown the client and bring koffing offline. Goodbye old friend.
	"""
	logger.info('Stopping main client...')
	await client.logout()


def ask_exit():
	"""
	Stop all tasks we have spawned before shutting down with return code 1.
	This signals koffing-ball.py that we should stop the run loop.
	"""
	logger.info('Stopping tasks...')
	global task_list
	for task in task_list:
		task.cancel()
	asyncio.ensure_future(exit())

	logger.info('Stopping...')
	sys.exit(1)  # return code > 0 means don't restart


"""
Bring koffing to life! Bring him to liiiiiife!!!!
"""
logger.info("Starting client...")
client.loop.create_task(timed_save())
client.run(TOKEN)
