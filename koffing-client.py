import discord
import asyncio
import sys
import time
import logging
import json
import operator
import os
from random import randint
from datetime import datetime
from datetime import timedelta

print("Welcome inside koffing's head")

def save_file(path, obj):
	'''
	Save the given data to the given file
	'''
	file = open(path, 'w')
	json_str = json.dumps(obj, sort_keys=True, indent=4)
	file.write(json_str)
	file.close()

def open_file(path, array):
	'''
	Return content of the file, or an empty array/map
	'''
	content = ''
	if not os.path.exists(path):
		if array:
			content = []
		else:
			content = {}
		save_file(path, content)
	elif not os.path.isfile(path):
		raise FileNotFoundError('{} does not exist as a file'.format(path))
		
	return open(path)

def turn_file_to_json(path, is_array):
	with (open_file(path, is_array)) as json_file:
		json_data = json.load(json_file)
		return json_data


if( len(sys.argv) < 2):
	TOKEN = input('Please enter token: ')
else:
	TOKEN = sys.argv[1].lstrip().rstrip()

START_MESSAGES = ["Koffing-bot, go~!", "Get 'em Koffing-bot~!"]
LOG_FORMAT = '[%(asctime)-15s] [%(levelname)s] [%(module)s.%(funcName)s] - %(message)s'
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
restart = True
date_format = '%Y-%m-%d'
pretty_date_format = '%a %b %Y %I:%M:%S %p'
cmd_prefix = '!'
#--------------------------------------------------------------------
#Logging set up
print("Setting up loggers...")

class ErrStreamToLogger(object):
	"""
	Fake stream-like object that redirects writes to a logger instance.
	"""
	def __init__(self, logger, log_level=logging.ERROR):
		self.logger = logger
		self.log_level = log_level
		self.linebuf = ''

	def write(self, buf):
		final = ''
		if not buf.isspace():
			for line in buf.lstrip().rstrip().splitlines():
				if line and not line.isspace():
					final = final + '\n' + line.lstrip() 
		self.logger.log(self.log_level, final.lstrip())

datetime_str = datetime.fromtimestamp(time.time()).strftime(date_format)

logging.basicConfig(format=LOG_FORMAT, level=logging.INFO)
log_dir = os.path.join(os.path.dirname(__file__), 'logs')

if not os.path.exists(log_dir):
	os.makedirs(log_dir)

logHandler = logging.FileHandler(os.path.join(os.path.dirname(__file__), 'logs', 'LOG_' + datetime_str + '.txt'), mode='a', encoding='utf-8')
logHandler.setLevel(logging.DEBUG)
logHandler.setFormatter(logging.Formatter(LOG_FORMAT))

logger = logging.getLogger(__name__)
logger.addHandler(logHandler)

logger.info("Stdout logger intialized")

err_logger = logging.getLogger('STDERR')
errHandler = logging.FileHandler(os.path.join(os.path.dirname(__file__), 'logs', 'ERR_' + datetime_str + '.txt'), mode='a', encoding='utf-8')
errHandler.setFormatter(logging.Formatter(LOG_FORMAT))

err_logger.addHandler(errHandler)

sys.stderr = ErrStreamToLogger(err_logger)
err_logger.info('###############################################')
err_logger.info('#-----------------NEW SESSION-----------------#')
err_logger.info('#------------------'+datetime_str+'-----------------#')
err_logger.info('###############################################')
#--------------------------------------------------------------------
#Control lists
logger.info("Loading settings...")

def load_settings():
	global settings, enabled, votes, skronks, authorized_guilds, authorized_channels, muted_channels, admin_users, game_str, SILENT_MODE, SAVE_TIMEOUT
	
	config_dir = os.path.join(os.path.dirname(__file__), 'config')
	if not os.path.exists(config_dir):
		os.makedirs(config_dir)

	settings = turn_file_to_json(CONFIG_FILE_PATH, False)
	enabled = turn_file_to_json(FEATURE_FILE_PATH, False)
	votes = turn_file_to_json(VOTE_FILE_PATH, False)
	skronks = turn_file_to_json(SKRONK_FILE_PATH, False)

	authorized_guilds = settings['authorized_guilds']
	authorized_channels = settings['authorized_channels']
	muted_channels = settings['muted_channels']
	admin_users = settings['admin_users']
	game_str = settings['game']
	SILENT_MODE = settings['silent_mode']
	SAVE_TIMEOUT = settings['save_timeout']

load_settings()

skronk_times = {}
task_list = []
#--------------------------------------------------------------------
#Finally, the main program!

client = discord.Client()

@client.event
@asyncio.coroutine
def on_ready():
	'''
	Called when the client has succesfully started up & logged in with our token
	'''
	logger.info('\n-----------------\nLogged in as %s - %s\n-----------------', client.user.name, client.user.id)
	if dev==True:
		logger.info('Member of the following guilds:')
		for guild in client.guild:
			logger.info('%s (%s)', guild.name, guild.id)

	new_game = discord.Game(name=game_str)
	yield from client.change_presence(game=new_game)

	for guild in client.guilds:
		if guild.id in guild:
			for channel in guild.channels:
				if channel.type==discord.ChannelType.text and can_message(guild, channel) and enabled['greeting']:
					logger.info('Alerting %s::%s to bot presence', guild.name, channel.id)
					yield from client.send_message(channel, START_MESSAGES[randint(0, len(START_MESSAGES)-1)])
	logger.info('Koffing-bot is up and running!')

@client.event
@asyncio.coroutine
def on_message(message):
	'''
	Fires when the client receieves a new message. Main starting point for message & command processing
	'''
	if None == message.channel or None == message.guild:
		yield from on_direct_message(message)
		return

	logger.info('Received message from "%s" (%s) in %s::%s', message.author.name, get_discriminating_name(message.author), message.guild.name, message.channel.name)
	if not authorized(message.guild, message.channel):
		logger.debug('Channel is unauthorized - not processing')
		return

	global game_str, SILENT_MODE, restart
	guild = message.guild
	channel = message.channel
	content = (message.content + '.')[:-1].lower()
	author = message.author

	# Koffing admin and config options
	if(content.startswith(cmd_prefix + 'koffing ')):
		content = content.replace(cmd_prefix + 'koffing', '', 1).lstrip().rstrip()
		yield from admin_console(message, content)

	# Actual commands and features:
	# Auto pin messages starting with #SotD
	# Voting (incl. leaderboards and history)
	# Skronking and skronk management

	#Sotd pinning
	elif content.startswith('#sotd'):
		if not enabled['sotd_pin']:
			logger.info("sotd_pin is not enabled")
			# Don't alert channel to pin disabled
			return
		logger.info('Pinning #SotD')
		yield from pin(message)

	# Voting
	elif content.startswith(cmd_prefix + 'vote'):
		if not enabled['voting']:
			yield from respond(message, "Voting is not enabled", emote="x")
		else:
			# check vote timeout & reset if needed
			content = content.replace(cmd_prefix + 'vote', '', 1).lstrip().rstrip()
			if content.startswith('leaderboard') or content.startswith('boards') or content.startswith('leaders'):
				yield from respond(message, get_vote_leaderboards(guild, author), True)
			elif content.startswith('history'):
				yield from respond(message, get_vote_history(guild, author), True)
			else:
				yield from place_vote(message)

	#Skronking
	elif content.startswith(cmd_prefix + 'skronk'):
		content = content.replace(cmd_prefix + 'skronk', '', 1).lstrip().rstrip()
		if not enabled['skronk']:
			logger.info('Skronking is not enabled -- not responding')
		elif content.startswith('timeout'):
			if not privileged(author):
				if not SILENT_MODE:
					yield from respond(message, "I'm afraid you can't do that {}".format(author.mention), emote="x")
				return
			content = content.replace('timeout', '', 1).lstrip().rstrip()
			if content.isdigit():
				old = skronk_timeout()
				settings['skronk_timeout'] = content
				yield from respond(message, 'Skronk timeout changed from {}s to {}s'.format(old, content))
			else:
				yield from respond(message, 'Please give a valid timeout in seconds', emote="x")
		elif content.startswith('clear') and privileged(author):
			content = content.replace('clear', '', 1).lstrip().rstrip()
			yield from clear_skronks(message, force=content.startswith('force'), user_clear=True)
		else:
			yield from skronk(message)

	elif content.startswith(cmd_prefix + 'remindme'):
		yield from remind_me(message)

	elif content.startswith(cmd_prefix + 'hype'):
		yield from hype(message)

	# Message content scanning
	else:
		if not message.author.id==client.user.id:
			yield from check_for_koffing(message)

def throw_chain():
	throw_chain1()

def throw_chain1():
	throw_chain2()

def throw_chain2():
	throw_chain3()

def throw_chain3():
	raise Exception("Koffing's Big Bad Exception")

@asyncio.coroutine
def admin_console(message, content):
	'''
	-Koffing admin and config options
	-Help
	-Admin management
	-Mute channels
	-Change game displayed
	-Manually save state
	-Shut down bot
	'''
	guild = message.guild
	channel = message.channel
	author = message.author

	if content.startswith('help'):
		yield from respond(message, HELP)

	if not privileged(author):
		yield from respond(message, "I'm afraid you can't do that {}".format(author.mention), emote="x")
		return

	#Admin management
	elif content.startswith('admin'):
		content = content.replace('admin', '', 1).lstrip().rstrip()
		if content.startswith('list'):
			yield from respond(message, get_admin_list(guild))
		elif (content.startswith('rm') or content.startswith('remove')):
			yield from remove_admin(message)
		elif content.startswith('add'):
			yield from add_admin(message)

	# Mute control (channel based). Stops koffing from listening and responding to channels on the list
	elif content.startswith('mute'):
		if not enabled["mute"]:
			yield from respond(message, 'Mute is not enabled', emote="x")
		else:
			yield from respond(message, "Koffing...")
			mute(guild, channel)

	#Unmute control. Gets koffing to listen to a channel again
	elif content.startswith('unmute'):
		if not enabled["mute"]:
			yield from respond(message, 'Mute is not enabled', emote="x")
		else:
			if muted(guild, channel):
				response, emoji = generate_koffing(guild)
				logger.info('Responding to "%s" (%s) in %s::%s', author.display_name, get_discriminating_name(author), guild.name, channel.id)
				yield from respond(message, response)
			unmute(guild, channel)

	# Game display
	elif content.startswith('game') or content.startswith('play'):
		if not enabled["game"]:
			yield from respond(message, 'Game is not enabled', emote="x")
		else:
			game_str = message.content[13:].lstrip().rstrip()
			logger.info("Setting bot to playing '{}'".format(game_str))
			yield from client.change_presence(game=discord.Game(name=game_str))

	# Manual save
	elif content.startswith('save'):
		save_all()
		yield from respond(message, "State saved.")

	# Load settings from disk
	elif content.startswith('reload'):
		load_settings()
		yield from respond(message, "Settings reloaded.")

	#Silent mode toggle
	elif content.startswith('quiet'):
		SILENT_MODE = not SILENT_MODE
		response, emoji = generate_koffing(message.guild)
		yield from respond(message, response)

	elif content.startswith('throw'):
		try:
			throw_chain()
		except Exception as e:
			err_logger.exception("Big bad error message incoming")


	# Kill bot
	elif content.startswith('return') or content.startswith('shutdown'):
		restart = False
		save_all()
		yield from shutdown_message(message)
		ask_exit()

	# Unrecognized command
	else:
		logger.info('Unknown command attempt from %s: [%s]', get_discriminating_name(author), (message.content + '.')[:-1].lower())
		yield from respond(message, "Skronk!", emote="x")

@asyncio.coroutine
def on_direct_message(message):
	'''
	C&C for direct messages, we get forwarded here from on_message()
	'''
	if message.author.id==client.user.id:
		return

	logger.info('Got a DM from %s', get_discriminating_name(message.author))
	content = message.content

	if content.startswith(cmd_prefix + 'remindme'):
		yield from remind_me(message)
	elif content.startswith(cmd_prefix):
		yield from admin_console(message, content.replace(cmd_prefix, '', 1))
	else:
		yield from direct_response(message, '')

@asyncio.coroutine
def timed_save():
	'''
	Loops until the bot shuts down, saving state (votes, settings, etc)
	'''
	while not client.is_closed:
		# Sleep first so we don't save as soon as we launch
		yield from asyncio.sleep(SAVE_TIMEOUT)
		if not client.is_closed:
			#could have closed between start of loop & sleep
			save_all()

@asyncio.coroutine
def shutdown_message(message):
	'''
	Saves state and then alerts all channels that it is shutting down
	'''
	for guild in client.guild:
		for channel in guild.channels:
			if channel.type==discord.ChannelType.text:
				if can_message(guild, channel) and enabled['greeting']:
					logger.info('Alerting %s::%s to bot shutdown', guild.name, channel.name)
					yield from client.send_message(channel, 'Koffing-bot is going back to its pokeball~!')
				elif message.guild == None or message.channel == None:
					continue
				elif guild.id == message.guild.id and channel.id == message.channel.id:
					logger.info('Alerting %s::%s to bot shutdown', guild.name, channel.name)
					yield from client.send_message(channel, 'Koffing-bot is going back to its pokeball~!')

@asyncio.coroutine
def check_for_koffing(message):
	'''
	Checks a message content for the word 'koffing' and gets excited if its there
	'''
	logger.debug('Checking for koffing...')
	if 'koffing' in message.content.lower() or client.user.mentioned_in(message):
		logger.debug('Found a koffing in the message!')

		if can_message(message.guild, message.channel) and enabled["text_response"]:
			# Quiet skip this, since that's the point of disabled text response
			if not SILENT_MODE:
				yield from client.send_typing(message.channel)

			response, emoji = generate_koffing(message.guild)
			asyncio.sleep(randint(0,1))
			yield from respond(message, response)
			if(emoji != None and not SILENT_MODE):
				yield from client.add_reaction(message, emoji)

		return #RETURN HERE TO STOP VOICE FROM HAPPENING BEFORE IT WORKS
		# need to figure out ffmpeg before this will work
		if message.author.voice_channel != None and enabled["voice_response"]:
			logger.debug('Attempting to play in voice channel %s', message.author.voice_channel.id)
			voice = voice_client_int(message.guild)
			if voice == None or voice.channel != message.author.voice_channel:
				voice = yield from client.join_voice_channel(message.author.voice_channel)
			player = voice.create_ffmpeg_player('koffing.mp3')
			player.start()

@asyncio.coroutine
def remind_me(message):
	'''
	Basic remindme functionality, works for seconds or minutes
	'''
	logger.info('Generating reminder for %s...', get_discriminating_name(message.author))
	contents = message.content.split(maxsplit=2)
	#['/remindme', 'time', 'message']
	if len(contents) < 3:
		yield from respond(message, "Skronk!", emote="x")
		return

	time = contents[1]
	# Check for units on end of string
	if not time.replace(".", "", 1).isdigit():
		if time.endswith('h'):
			time = str(float(time[:-1])*3600)
		if time.endswith('m'):
			time = str(float(time[:-1])*60)
		elif time.endswith('s'):
			time = str(float(time[:-1])*1)
		if not time.replace(".", "", 1).isdigit():
			yield from respond(message, "Skronk!", emote="x")
			return

	wakeup = (datetime.now() + timedelta(seconds=int(float(time)))).strftime(pretty_date_format)
	logger.info('Reminder for %s in %s seconds (%s)', get_discriminating_name(message.author), time, wakeup)
	# Respond based on the length of time to wait
	yield from direct_response(message, "Alright, reminding you at {}".format(wakeup))


	if(message.guild != None):
			yield from koffing_reaction(message)
	task_list.append(client.loop.create_task(delayed_response(message, "{} this is your reminder:\n{}{}".format(message.author.mention, " "*11, contents[2]), float(time))))
	return

@asyncio.coroutine
def hype(message):
	'''
	Beefs up the message and parrots it back
	'''
	logger.info('Hyping message!')
	phrase = message.content.replace('/hype', '', 1).lstrip().rstrip()
	if phrase == "":
		yield from respond(message, "Skronk!", emote="x")
		return
	hyped = "***{}***  boyooooooo".format(" ".join(phrase).upper())
	yield from respond(message, hyped, True)

@asyncio.coroutine
def delayed_response(message, content, time=300):
	'''
	Sleeps for time seconds and then responds to the message author with the given content
	'''
	yield from asyncio.sleep(time)
	if not client.is_closed:
		yield from direct_response(message, content)

@asyncio.coroutine
def add_admin(message):
	'''
	Add the mentioned members to the bot admin list
	'''
	users = message.mentions
	channel = message.channel
	for user in users:
		user_str = get_discriminating_name(user)
		if user_str not in admin_users:
			msg_str = 'Added {} to the admin list.'.format(user.mention)
			logger.info('' + msg_str)
			admin_users.append(user_str)
			yield from respond(message, msg_str)
	logger.info('Done adding admins.')

@asyncio.coroutine
def remove_admin(message):
	'''
	Remove the mentioned members from the bot admin list
	'''
	users = message.mentions
	channel = message.channel
	for user in users:
		user_str = get_discriminating_name(user)
		if user_str in admin_users:
			msg_str = 'Removed {} from the admin list.'.format(user.mention)
			logger.info('' + msg_str)
			admin_users.remove(user_str)
			yield from respond(message, msg_str)
	logger.info('Done removing admins.')

@asyncio.coroutine
def respond(message, text, ignore_silent=False, emote="koffing"):
	'''
	Respond to a message from a channel; puts line in logs
	'''

	#Make sure a DM didn't show up here somehow
	if message.channel == None:
		yield from direct_response(message, text)
		return

	#Mute response if we're running in silent mode and we aren't overriding
	if SILENT_MODE and not ignore_silent:
		logger.info('Muted response to "%s" (%s) in %s::%s',
				message.author.display_name,
				get_discriminating_name(message.author),
				message.guild.name, 
				message.channel.id)
		if emote == "koffing":
			yield from koffing_reaction(message)
		elif emote == "ok":
			yield from positive_reaction(message)
		elif emote == "x": 
			yield from negative_reaction(message)
	else:
		#Standard respond
		if not muted(message.guild, message.channel):
			logger.info('Responding to "%s" (%s) in %s::%s', message.author.display_name, get_discriminating_name(message.author), message.guild.name, message.channel.id)
			if SILENT_MODE:
				logger.debug('Loud response requested!')
			yield from client.send_message(message.channel, text)

@asyncio.coroutine
def direct_response(message, text):
	'''
	Reply directly to a DM
	'''
	logger.info('Responding to DM from %s', get_discriminating_name(message.author))
	if(text == ''):
		yield from client.send_message(message.author, ':eyes:')
	else:
		yield from client.send_message(message.author, text)
	return

@asyncio.coroutine
def negative_reaction(message):
	'''
	React negatively to the message
	'''
	emoji = get_x_emoji(message.guild)
	if emoji == None or emoji == '':
		logger.info('Got a blank value for X emote, no reaction possible')
	else:
		logger.info('Reacting with a negative emoji')
		yield from client.add_reaction(message, emoji)

@asyncio.coroutine
def positive_reaction(message):
	'''
	React positively to the message
	'''
	emoji = get_ok_emoji(message.guild)
	if emoji == None or emoji == '':
		logger.info('Got a blank value for ok_hand emote, no reaction possible')
	else:
		logger.info('Reacting with a positive emoji')
		yield from client.add_reaction(message, emoji)

@asyncio.coroutine
def koffing_reaction(message):
	'''
	React koffing-ly to the message
	'''
	emoji = get_koffing_emoji(message.guild)
	if emoji == None or emoji == '':
		logger.info('Got a blank value for koffing emote, no reaction possible')
	else:
		logger.info('Reacting with a koffing emoji')
		yield from client.add_reaction(message, emoji)

@asyncio.coroutine
def pin(message):
	'''
	Pins a message
	'''
	logger.info('Pinning message')
	try:
		yield from koffing_reaction(message)
		yield from client.pin_message(message)
	except NotFound:
		err_logger.warn('Message or channel has been deleted, pin failed')
	except Forbidden:
		err_logger.warn('Koffing-bot does not have sufficient permissions to pin in %s::%s', guild.name, channel.id)
	except (Error, Exception) as e:
		err_logger.error('Could not pin message: {}'.format(e))

@asyncio.coroutine
def place_vote(message):
	'''
	Adds a vote for @member or @role or @everyone
	'''
	logger.info('Tallying votes...')

	if len(message.mentions) == 0 and len(message.role_mentions) == 0 and not message.mention_everyone:
		yield from respond(message, "Tag someone to vote for them!", emote="x")
		return

	vote_getters = get_mentioned(message)
	voted_for_self = False
	names = ''
	for member in vote_getters:
		name = get_discriminating_name(member)

		if member.id == message.author.id:
			yield from respond(message, cmd_prefix + "skronk {} for voting for yourself...".format(message.author.mention), True)
			voted_for_self = True
			continue #cannot vote for yourself

		names += member.mention + ", "
		cur_votes, start_time = get_current_votes()
		if cur_votes == None:
			cur_votes = {name: 1}
			votes[date_to_string(datetime.now().date())] = cur_votes
		else:
			if name in cur_votes:
				cur_votes[name] = cur_votes[name] + 1
			else:
				cur_votes[name] = 1
			votes[start_time] = cur_votes

	names = names.rstrip(', ')
	if len(names) > 0:
		yield from respond(message, 'Congratulations {}! You got a vote!{}'.format(names, get_vote_leaderboards(message.guild, message.author, False)))
	elif not voted_for_self:
		yield from respond(message, "You didn't tag anyone you can vote for {}".format(message.author.mention), emote="x")

@asyncio.coroutine
def skronk(message):
	'''
	Skronks @member
	'''
	logger.info('Skronking..')

	global skronk_times
	skronk = get_skronk_role(message.guild)
	if skronk == None:
		yield from respond(message, "There will be no skronking here.", emote="x")
		return

	skronked = get_mentioned(message)
	if len(skronked) == 0:
		yield from respond(message, "Tag someone to skronk them!", emote="x")
		return

	# Is the author skronked already?
	if is_skronked(message.author, message.guild, skronk):
		yield from respond(message, "What is skronked may never skronk.", emote="x")
		return

	no_skronk = []
	skronk_em = False
	for member in skronked:
		# Is the author trying to skronk himself?
		if member == message.author:
			yield from respond(message, "You can't skronk yourself {}... let me help you with that.".format(message.author.mention), True)
			skronk_em = True
			no_skronk.append(member)
			continue

		# Are they trying to skronk the skronker???
		if member.id == client.user.id:
			yield from respond(message, "You tryna skronk me??", True)
			skronk_em = True
			no_skronk.append(member)
			continue

	#Clean up list of skronkees
	for member in no_skronk:
		if member in skronked:
			skronked.remove(member)

	if skronk_em:
		yield from respond(message, cmd_prefix + "skronk {}".format(message.author.mention), True)
	# Okay, let's do the actual skronking
	for member in skronked:
		if member.id in skronks:
			skronks[member.id] += 1
		else:
			skronks[member.id] = 1
		if member.id in skronk_times:
			skronk_times[member.id] = int(skronk_times[member.id]) + int(skronk_timeout())
		else:
			skronk_times[member.id] = int(skronk_timeout())
			task_list.append(client.loop.create_task(remove_skronk(member, message)))
		yield from client.add_roles(member, skronk)
		yield from respond(message, "{} got SKRONK'D!!!! ({}m left)".format(member.mention, str(get_skronk_time(member.id))))

@asyncio.coroutine
def remove_skronk(member, message, silent=False, wait=True, absolute=False, user_clear=False):
	'''
	Removes @member from skronk
	'''
	global skronk_times
	if wait:
		yield from asyncio.sleep(int(skronk_timeout()))
	logger.info('Attempting to deskronk {}'.format(get_discriminating_name(member)))

	if member.id in skronk_times:
		skronk_times[member.id] = int(skronk_times[member.id]) - int(skronk_timeout())
		if int(skronk_times[member.id]) == 0 or absolute or user_clear:
			del skronk_times[member.id]
		else:
			logger.info('Skronk has not yet expired!')
			yield from respond(message, "Only {}m of shame left {}".format(str(get_skronk_time(member.id)), member.mention))
			task_list.append(client.loop.create_task(remove_skronk(member, message, silent, wait, absolute)))
			return

	skronk = get_skronk_role(message.guild)
	if skronk != None and skronk in member.roles:
		yield from client.remove_roles(member, skronk)
		if not silent:
			yield from respond(message, "You're out of skronk {}!".format(member.mention))

@asyncio.coroutine
def clear_skronks(message, force=False, user_clear=False):
	'''
	Clears all skronks. If this is not a forced clear, it will not happen if the author is skronked
	'''
	logger.info('Attempting to clear all skronks...')

	if not privileged(message.author):
		yield from respond(message, "I'm afraid you can't do that {}".format(author.mention), emote="x")
		return

	role = get_skronk_role(message.guild)
	if role in message.author.roles and not force:
		yield from respond(message, "You can't do that..", emote="x")
		if not SILENT_MODE:
			yield from respond(message, cmd_prefix + "skronk {}".format(message.author.mention))
		return

	tagged = get_mentioned(message)
	skronked = members_of_role(message.guild, role)
	names = ""
	if len(tagged) > 0:
		for member in tagged:
			if role in member.roles:
				yield from remove_skronk(member, message, silent=True, wait=False, absolute=force, user_clear=True)
				names += member.mention + ", "
	else:
		for member in skronked:
			yield from remove_skronk(member, message, silent=True, wait=False, absolute=force, user_clear=True)
			names += member.mention + ", "
	names = names.rstrip(', ')
	
	if len(names) > 0:
		yield from respond(message, "Hey {}... Your skronkin' lil ass was just saved by {}!".format(names, message.author.mention))
	else:
		yield from respond(message, "There was no one to remove from skronk...", emote="x")

def get_skronk_time(member_id):
	'''
	Gets the time left for a user specific id and returns it in minutes
	'''
	if not member_id in skronk_times:
		return 0
	return int(int(skronk_times[member_id])/60)

def skronk_timeout():
	return int(settings['skronk_timeout'])

def get_mentioned(message, everyone=True):
	'''
	Gets everyone mentioned in a message. Aggregates members from all roles mentioned
	'''
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
			if(member.permissions_in(message.channel).read_messages):
				mentioned.append(member)

	seen = set()
	mentioned = [x for x in mentioned if x not in seen and not seen.add(x)]
	return mentioned

def members_of_role(guild, role):
	'''
	Returns an array of all members for the given role in the given guild
	'''
	logger.info("Looking for all members of {}".format(role.name))
	ret = []
	for member in guild.members:
		if role in member.roles:
			ret.append(member)
	return ret

def get_skronk_role(guild):
	'''
	Finds the role named SKRONK'D
	'''
	logger.info("Looking for skronk role...")
	for role in guild.roles:
		if role.name.lower() == SKRONKED.lower():
			return role
	logger.info("Did not find role named {}".format(SKRONKED))
	return None

def is_skronked(member, guild, skronk):
	'''
	Returns true if the member is skronked in this guild
	'''
	if skronk == None:
		return False

	for role in member.roles:
		if role == skronk:
			return True
	return False

def get_admin_list(guild):
	'''
	Gets a string containing the list of bot admins
	'''
	logger.info('Obtaining admin list')
	admin_str = 'listens to the following trainers:\n'
	for user in admin_users:
		admin = guild.get_member_named(user)
		if admin != None:
			admin_str += ' -' + admin.mention + '\n'
	return admin_str

def get_vote_leaderboards(guild, requester, call_out=True):
	'''
	Returns a string of the current vote leaderboard
	'''
	logger.info('Compiling vote leaderboards...')
	guild_leaders = []
	cur_votes, start = get_current_votes()
	if(cur_votes == None):
		return 'No one in {} has recieved any votes!'.format(guild.name)

	for user_name in cur_votes:
		member = guild.get_member_named(user_name)
		if member != None:
			guild_leaders.append((member, cur_votes[user_name]))

	if len(guild_leaders) == 0:
		return 'No one in {} has recieved any votes!'.format(guild.name)

	sorted_ch_lead = sorted(guild_leaders, key=lambda tup: tup[1], reverse=True)

	leaders = []
	idx = 0
	username = get_discriminating_name(sorted_ch_lead[idx][0])
	score = sorted_ch_lead[idx][1]
	top_score = score

	while(score == top_score):
		member = sorted_ch_lead[idx][0]
		if(member != None):
			leaders.append(member)
		idx = idx + 1
		if(len(sorted_ch_lead) > idx ):
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

	leaderboard_str = '\n \nLeaderboard for week of {}\n{}\nVotes close on {}```'.format(start, leader_str, date_to_string(string_to_date(start) + timedelta(7)))
	for tup in sorted_ch_lead:
		leaderboard_str += '{}: {}'.format(get_user_name(tup[0]), tup[1])
		if requester.name == tup[0].name and call_out:
			leaderboard_str +='<-- It\'s you!\n'
		else:
			leaderboard_str +='\n'
	leaderboard_str +='```'
	return leaderboard_str

def get_vote_history(guild, requestor):
	'''
	Returns a string of all the winners of each recorded voting session
	'''
	logger.info('Compiling vote winners...')

	leaders = []
	cur_votes, start = get_current_votes()
	for date in votes:
		if string_to_date(date) < string_to_date(start) and string_to_date(date) - string_to_date(start) > timedelta(-8):
			if(len(votes[date]) > 0):
				sorted_users = sorted(votes[date], key=lambda tup: tup[1], reverse=False)
				idx = 0
				top_score = votes[date][sorted_users[idx]]
				username = sorted_users[idx]
				score = votes[date][username]

				while(score == top_score):
					member = guild.get_member_named(username)
					if(member != None):
						leaders.append([date, member, score])
					idx = idx + 1
					if(len(sorted_users) > idx ):
						username = sorted_users[idx]
						score = votes[date][username]
					else:
						score = -1

	history_str = 'All-time voting history:```'
	current_date = None

	if(len(leaders) == 0):
		history_str = "This guild has no vote winners..."
	else:
		leaders = sorted(leaders, key=lambda tup: datetime.strptime(tup[0], pretty_date_format))
		for tup in leaders:
			if(tup[0] != current_date):
				current_date = tup[0]
				history_str += '\n{} - {}: {}'.format(tup[0], get_user_name(tup[1]), tup[2])
			else:
				history_str += '\n             {}: {}'.format(get_user_name(tup[1]), tup[2])
		history_str += '```'

	return history_str

def get_user_name(user):
	'''
	Gets a pretty string of a user's name and nickname or just name, if there is no nickname
	'''
	if(user.nick != None):
		return user.name + ' (' + user.nick + ')'
	else:
		return user.name

def get_current_votes():
	'''
	Get the votes map for the current session
	'''
	now = datetime.now().date()
	for start in votes:
		if(now - string_to_date(start) < timedelta(7)):
			return votes[start], start
	return None, None

def date_to_string(date):
	'''
	Turn a date object into a string formatted the way we want (YYYY-mm-dd)
	'''
	return date.strftime(pretty_date_format)

def string_to_date(string):
	'''
	Turn a string in YYYY-mm-dd into a date object
	'''
	return datetime.strptime(string, pretty_date_format).date()

def can_message(guild, channel):
	'''
	True if the bot is authorized and unmuted for the channel, False otherwise
	'''
	return authorized(guild, channel) and not muted(guild, channel)

def privileged(user):
	'''
	True if this user is a bot admin, False otherwise
	'''
	return get_discriminating_name(user) in admin_users

def get_discriminating_name(user):
	'''
	Returns a string of the form <Username>#<USERDISCRIMINATOR>
	'''
	return '{}#{}'.format(user.name, user.discriminator)

def authorized(guild, channel):
	'''
	True if the bot is authorized in this channel
	'''
	if guild.id in authorized_guild:
		return channel.id in authorized_channels[guild.id]
	return False

def muted(guild, channel):
	'''
	True if the bot is muted in this channel
	'''
	if guild.id in muted_channels:
		return channel.id in muted_channels[guild.id]
	return False

def mute(guild, channel):
	'''
	Adds the channel to the muted list
	'''
	logger.info('Muting channel {}::{}...', guild.name, channel.name)
	if guild.id in muted_channels:
		if channel.id not in muted_channels[guild.id]:
			muted_channels[guild.id].append(channel.id)
	else:
		muted_channels[guild.id] = [channel.id]

def unmute(guild, channel):
	'''
	Removes the channel from the muted list
	'''
	logger.info('Unmuting channel {}::{}...', guild.name, channel.name)
	if guild.id in muted_channels:
		if channel.id in muted_channels[guild.id]:
			muted_channels[guild.id].remove(channel.id)

def get_date():
	'''
	Returns a string of the current date in mm-dd-YYYY
	'''
	return datetime.fromtimestamp(time.time()).strftime('%m-%d-%Y')

def generate_koffing(guild):
	'''
	Returns a string of a happy koffing
	'''
	koffing_emoji = get_koffing_emoji(guild)
	koffing_str = None
	response = None

	koffing_core_str = 'K' + randint(1,2)*'o' + 'ff' + randint(1,4)*'i' + 'ng' 
	if(randint(1,3)==1):
		koffing_core_str = koffing_core_str + randint(1,3)*'?'
	else:
		koffing_core_str = koffing_core_str + randint(1,5)*'!'

	if koffing_emoji != None:
		num_koffs = randint(2,5)
		koffing_str = str(koffing_emoji)
		response = num_koffs*koffing_str + ' ' + koffing_core_str + ' ' + num_koffs*koffing_str
	else:
		response = koffing_core_str
	return response, koffing_emoji

def get_koffing_emoji(guild):
	'''
	Returns the koffing emoji if this guild has one, None otherwise
	'''
	return_emoji = ''
	if guild == None:
		return return_emoji

	for emoji in guild.emojis:
		if emoji.name == 'koffing':
			return_emoji = emoji
	return return_emoji

def get_ok_emoji(guild):
	'''
	Returns the checkmark emoji
	'''
	return '\N{OK Hand Sign}'

def get_x_emoji(guild):
	'''
	Returns the checkmark emoji
	'''
	return '\N{Cross Mark}'

def save_all(silent=False):
	'''
	Perform all saves
	'''
	if not silent:
		logger.info('Saving to disk...')
	save_config(True)
	save_feature_toggle(True)
	save_votes(True)
	save_skronk(True)

def save_config(silent=False):
	'''
	Save the configuration file
	'''
	contents = {'authorized_channels': authorized_channels, 'authorized_guilds': authorized_guilds, 'muted_channels': muted_channels, 'admin_users': admin_users, 'game': game_str, 'skronk_timeout': skronk_timeout(), 'silent_mode': SILENT_MODE, 'save_timeout': SAVE_TIMEOUT}
	if not silent:
		logger.info('Writing settings to disk...')
	save_file(CONFIG_FILE_PATH, contents)

def save_feature_toggle(silent=False):
	'''
	Save feature toggle map
	'''
	if not silent:
		logger.info("Writing features to disk...")
	save_file(FEATURE_FILE_PATH, enabled)

def save_votes(silent=False):
	'''
	Save vote map
	'''
	if not silent:
		logger.info('Writing votes to disk...')
	save_file(VOTE_FILE_PATH, votes)

def save_skronk(silent=False):
	'''
	Save skronk list
	'''
	if not silent:
		logger.info('Saving skronk...')
	save_file(SKRONK_FILE_PATH, skronks)

@asyncio.coroutine                                       
def exit():
	'''
	Shutdown the client and bring koffing offline. Goodbye old friend.
	'''
	logger.info('Stopping main client...')                                        
	yield from client.logout()

def ask_exit():
	'''
	Stop all tasks we have spawned before shutting down
	'''
	logger.info('Stopping tasks...')
	global task_list
	for task in task_list:
		task.cancel()
	asyncio.ensure_future(exit())

'''
Bring koffing to life! Bring him to liiiiiife!!!!
'''
logger.info("Starting client...")
client.loop.create_task(timed_save())
client.run(TOKEN)