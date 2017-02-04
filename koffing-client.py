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

if( len(sys.argv) != 2):
	TOKEN = input('Please enter token: ')
else:
	TOKEN = sys.argv[1].lstrip().rstrip()

LOG_FORMAT = '[%(asctime)-15s] [%(levelname)s] - %(message)s'
FEATURE_LIST = '```Current feature list (*=requires privilege):\n -responds in text channels!\n -responds in voice channels (PLANNED)\n -roll call (PLANNED)\n -song of the day pinning!\n -elo lookup [Overwatch] (PLANNED) \n -elo lookup [LoL] (PLANNED) \n -mute\n -vote!```'
HELP = 'Koffing~~ I will respond any time my name is called!```\nCommands (*=requires privilege):\n /koffing help\n /koffing features\n*/koffing mute\n*/koffing unmute\n*/koffing admin [list] [remove (@user) [@user]] [add (@user) [@user]]\n*/koffing play [name]\n*/koffing return```'
CONFIG_FILE_NAME = 'koffing.cfg'
CONFIG_FILE_PATH = os.path.join(os.path.dirname(__file__), CONFIG_FILE_NAME)
FEATURE_FILE_NAME = "feature_toggle.cfg"
FEATURE_FILE_PATH = os.path.join(os.path.dirname(__file__), FEATURE_FILE_NAME)
VOTE_FILE_NAME = 'vote_count'
VOTE_FILE_PATH = os.path.join(os.path.dirname(__file__), VOTE_FILE_NAME)
SKRONK_FILE_NAME = 'skronk'
SKRONK_FILE_PATH = os.path.join(os.path.dirname(__file__), SKRONK_FILE_NAME)
SKRONKED = "SKRONK'D"
SAVE_TIMEOUT = 1800
start_messages = ["Koffing-bot, go~!", "Get 'em Koffing-bot~!"]
dev = True
#--------------------------------------------------------------------
#Logging set up
date = datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d')
logging.basicConfig(format=LOG_FORMAT, level=logging.INFO)
logger = logging.getLogger(__name__)
fh = logging.FileHandler(os.path.join(os.path.dirname(__file__), "LOG_" + date + ".txt"))
fh.setLevel(logging.DEBUG)
fh.setFormatter(logging.Formatter(LOG_FORMAT))
logger.addHandler(fh)
#--------------------------------------------------------------------
#Control lists
settings = json.load(open(CONFIG_FILE_PATH))
authorized_servers = settings['authorized_servers']
authorized_channels = settings['authorized_channels']
muted_channels = settings['muted_channels']
admin_users = settings['admin_users']
game_str = settings['game'] 

enabled = json.load(open(FEATURE_FILE_PATH))
#--------------------------------------------------------------------
votes = json.load(open(VOTE_FILE_PATH))
skronks = json.load(open(SKRONK_FILE_PATH))
child_threads = []
#--------------------------------------------------------------------
client = discord.Client()


@client.event
@asyncio.coroutine
def on_ready():
	
	logger.info('\n-----------------\nLogged in as %s - %s\n-----------------', client.user.name, client.user.id)    
	if dev==True:
		logger.info('Member of the following servers:')
		for server in client.servers:
			logger.info(' %s (%s)', server.name, server.id)

	new_game = discord.Game(name=game_str)
	yield from client.change_presence(game=new_game)

	for server in client.servers:
		if server.id in authorized_servers:
			for channel in server.channels:
				if channel.type==discord.ChannelType.text and can_message(server, channel) and enabled['greeting']:
					logger.info('Alerting %s::%s to bot presence', server.name, channel.id)
					yield from client.send_message(channel, start_messages[randint(0, len(start_messages)-1)])
				

@client.event
@asyncio.coroutine
def on_message(message):
	logger.info('Received message from "%s" (%s) in %s::%s', message.author.display_name, get_discriminating_name(message.author), message.server.name, message.channel.id)
	if not authorized(message.server, message.channel):
		if message.author.id == client.user.id:
			yield from respond(message, "{} remove me from your server.".format(message.author.mention))
		return

	global game_str
	server = message.server
	channel = message.channel
	content = (message.content + '.')[:-1].lower()
	author = message.author

	# Koffing admin and config options
	# Feature list
	# Help
	# Admin management
	# Mute channels
	# Change game displayed
	# Manually save state
	# Shut down bot
	if(content.startswith('/koffing ')):
		content = content.replace('/koffing', '', 1).lstrip().rstrip()

		# Help
		if content.startswith('help'):
			yield from respond(message, HELP)        

		# Feature list
		elif content.startswith('feature'):
			if not enabled['features']:
				yield from respond(message, 'The feature list is not enabled')
			else:
				yield from respond(message, FEATURE_LIST)

		#Admin management
		elif content.startswith('admin'):
			content = content.replace('admin', '', 1).lstrip().rstrip()
			if not privileged(author):
				yield from respond(message, "I'm afraid you can't do that {}".format(author.mention))
			elif content.startswith('list'):
				yield from respond(message, get_admin_list(server))
			elif (content.startswith('rm') or content.startswith('remove')):
				yield from remove_admin(message)
			elif content.startswith('add'):
				yield from add_admin(message)

		# Mute control
		elif content.startswith('mute'):
			if not privileged(author):
				yield from respond(message, "I'm afraid you can't do that {}".format(author.mention))
			elif not enabled["mute"]:
				yield from respond(message, 'Mute is not enabled')
			else:
				yield from respond(message, "Koffing...")
				mute(server, channel)

		#Unmute control
		elif content.startswith('unmute'):
			if not privileged(author):
				yield from respond(message, "I'm afraid you can't do that {}".format(author.mention))
			elif not enabled["mute"]:
				yield from respond(message, 'Mute is not enabled')
			else:
				if muted(server, channel):
					response, emoji = generate_koffing(server)
					logger.info('  Responding to "%s" (%s) in %s::%s', author.display_name, get_discriminating_name(author), server.name, channel.id)
					yield from client.send_message(channel, response)
				unmute(server, channel)

		# Game display
		elif content.startswith('game') or content.startswith('play'):
			if not privileged(author):
				yield from respond(message, "I'm afraid you can't do that {}".format(author.mention))
			elif not enabled["game"]:
				yield from respond(message, 'Game is not enabled')
			else:
				game_str = message.content[13:].lstrip().rstrip()
				logger.info("  Setting bot to playing '{}'".format(game_str))
				yield from client.change_presence(game=discord.Game(name=game_str))

		# Manual save 
		elif content.startswith('save'):
			save_all()

		# Kill bot
		elif content.startswith('return'):
			if not privileged(author):
				yield from respond(message, "I'm afraid you can't do that {}".format(author.mention))
			else:
				yield from shutdown_message()
				yield from client.logout()

		# Unrecognized command
		else:
			yield from respond(message, "Skronk!")


	# Actual commands and features:
	# Auto pin messages starting with #SotD
	# Voting (incl. leaderboards and history)
	# Skronking and skronk management

	#Sotd pinning
	elif content.startswith('#sotd'):
		if not enabled['sotd_pin']:
			logger.info("  sotd_pin is not enabled")
			# Don't alert channel to pin disabled
			return
		logger.info('  Pinning #SotD')
		yield from pin(message)

	# Voting 
	elif content.startswith('/vote'):
		if not enabled['voting']:
			yield from respond(message, "Voting is not enabled")
		else:
			# check vote timeout & reset if needed
			content = content.replace('/vote', '', 1).lstrip().rstrip()
			if content.startswith('leaderboard') or content.startswith('boards') or content.startswith('leaders'):
				yield from respond(message, get_vote_leaderboards(server, author))
			elif content.startswith('history'):
				yield from respond(message, get_vote_history(server, author))
			else:
				yield from place_vote(message)

	#Skronking
	elif content.startswith('/skronk'):
		content = content.replace('/skronk', '', 1).lstrip().rstrip()
		if not enabled['skronk']:
			logger.info('  Skronking is not enabled -- not responding')
		elif content.startswith('timeout') and privileged(author):
			content = content.replace('timeout', '', 1).lstrip().rstrip()
			if content.isdigit():
				old = settings['skronk_timeout']
				settings['skronk_timeout'] = content
				yield from respond(message, 'Skronk timeout changed from {}s to {}s'.format(old, content))
			else:
				yield from respond(message, 'Please give a valid timeout in seconds')
		elif content.startswith('clear') and privileged(author):
			content = content.replace('clear', '', 1).lstrip().rstrip()
			if(content.startswith('force')):
				yield from clear_skronks(message, True)
			else:
				yield from clear_skronks(message)
		else:
			yield from skronk(message)

	# Message content scanning
	else:
		if not message.author.id==client.user.id:
			yield from check_for_koffing(message)
			# yield from check_for_thicc(message)

@asyncio.coroutine
def timed_save():
	'''Loops until the bot shuts down, saving state (votes, settings, etc)'''
	while not client.is_closed:
		# Sleep first so we don't save as soon as we launch
		yield from asyncio.sleep(SAVE_TIMEOUT)
		save_all()

@asyncio.coroutine
def shutdown_message():
	'''Saves state and then alerts all channels that it is shutting down'''
	save_all()
	for server in client.servers:
		for channel in server.channels:
			if channel.type==discord.ChannelType.text and can_message(server, channel) and enabled['greeting']:
				logger.info('Alerting %s::%s to bot shutdown', server.name, channel.id)
				yield from client.send_message(channel, 'Koffing-bot is going back to its pokeball~!')              

@asyncio.coroutine
def check_for_koffing(message):
	'''Checks a message content for the word 'koffing' and gets excited if its there'''
	if 'koffing' in message.content.lower() or client.user.mentioned_in(message):

		if can_message(message.server, message.channel) and enabled["text_response"]:
			# Quiet skip this, since that's the point of disabled text response
			yield from client.send_typing(message.channel)
			response, emoji = generate_koffing(message.server)
			asyncio.sleep(randint(0,3))
			yield from respond(message, response)
			if(emoji != None and emoji != ""):
				yield from client.add_reaction(message, emoji)

		return #RETURN HERE TO STOP VOICE FROM HAPENING BEFORE IT WORKS
		# need to figure out ffmpeg before this will work
		if message.author.voice_channel != None and enabled["voice_response"]:
			logger.debug('Attempting to play in voice channel %s', message.author.voice_channel.id)
			voice = voice_client_int(message.server)
			if voice == None or voice.channel != message.author.voice_channel:
				voice = yield from client.join_voice_channel(message.author.voice_channel)
			player = voice.create_ffmpeg_player('koffing.mp3')
			player.start()

def check_for_thicc(message):
	return

@asyncio.coroutine
def add_admin(message):
	'''Add the mentioned members to the bot admin list'''
	users = message.mentions 
	channel = message.channel
	for user in users:
		user_str = get_discriminating_name(user)
		if user_str not in admin_users:
			admin_users.append(user_str)
			yield from respond(message, "Added {} to the admin list.".format(user.mention))

@asyncio.coroutine
def remove_admin(message):
	'''Remove the mentioned members from the bot admin list'''
	users = message.mentions
	channel = message.channel
	for user in users:
		user_str = get_discriminating_name(user)
		if user_str in admin_users:
			admin_users.remove(user_str)
			yield from respond(message, "Removed {} from the admin list.".format(user.mention))

@asyncio.coroutine
def respond(message, text):
	'''Respond to a message from a channel; puts line in logs'''
	if not muted(message.server, message.channel):
		logger.info('  Responding to "%s" (%s) in %s::%s', message.author.display_name, get_discriminating_name(message.author), message.server.name, message.channel.id)
		yield from client.send_message(message.channel, text)

@asyncio.coroutine
def pin(message):
	'''Pins a message'''
	try:
		emoji = get_koffing_emoji(message.server)
		if emoji != None:
			yield from client.add_reaction(message, emoji)
		yield from client.pin_message(message)
	except NotFound:
		logger.warn('Message or channel has been deleted, pin failed')
	except Forbidden:
		logger.warn('Koffing-bot does not have sufficient permissions to pin in %s::%s'.format(server.name, channel.id))
	except (Error, Exception) as e:
		logger.error('Could not pin message: {}'.format(e))

@asyncio.coroutine
def place_vote(message):
	'''Adds a vote for @member or @role or @everyone'''
	if len(message.mentions) == 0 and len(message.role_mentions) == 0 and not message.mention_everyone:
		yield from respond(message, "You need to tag someone to vote for them!")
		return

	vote_getters = []
	group_message = ''
	if len(message.mentions) > 0:
		member = message.mentions[0]
		name = get_discriminating_name(member)
		vote_getters.append([name, member, True])

		check = message.content.replace('/vote', '', 1).lstrip().rstrip()
		if not check.lstrip().rstrip().startswith(member.mention):
			logger.info("  Could not calculate vote: '{}', looking for {}".format(check, member.mention))
			yield from respond(message, "Skronk!")
			return
	elif len(message.role_mentions) > 0:
		role = message.role_mentions[0]

		check = message.content.replace('/vote', '', 1).lstrip().rstrip()
		if not check.lstrip().rstrip().startswith(role.mention):
			logger.info("  Could not calculate vote: '{}', looking for {}".format(check, member.mention))
			yield from respond(message, "Skronk!")
			return

		for member in members_of_role(message.server, role):
			vote_getters.append([get_discriminating_name(member), member, False])

		if len(vote_getters) > 0:
			group_message = 'Ayyy congrats {}!! You get a vote!'.format(role.mention)
		else:
			group_message = '/skronk {} voting for an empty group'.format(message.author)
	else:
		for member in message.server.members:
			vote_getters.append([get_discriminating_name(member), member, False])
		group_message = 'Everyone gets a vote!!!!!'
		
	for named_member in vote_getters: 
		name = named_member[0]
		member = named_member[1]
		announce = named_member[2]
		
		if member.id == message.author.id:
			if announce:
				yield from respond(message, "You can't vote for yourself {}....".format(member.mention))
			continue
		
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

		if announce:
			yield from respond(message, "{}, you just got a vote! Total votes: {}".format(member.mention, cur_votes[name]))

	if group_message != '':
		yield from respond(message, group_message)
		yield from respond(message, get_vote_leaderboards(message.server, message.author))

@asyncio.coroutine
def skronk(message):
	'''Skronks @member'''
	if len(message.mentions) == 0:
		yield from respond(message, "You need to tag someone to vote for them!")
		return

	member = message.mentions[0]
	name = get_discriminating_name(member)
	
	check = message.content.replace('/skronk', '', 1)
	skronk = get_skronk_role(message.server)

	if not check.lstrip().rstrip().startswith(member.mention):
		yield from respond(message, 'Sk-RONK!!')
		return

	if skronk == None:
		yield from respond(message, "There's no skronk role here!")
		return

	# Is the author skronked already?
	for role in message.author.roles:
		if role == skronk:
			yield from respond(message, "What is skronked may never skronk.")
			return

	# Is the target already skronked?
	for role in member.roles:
		if role == skronk:
			yield from respond(message, "{} was already skronked.. you skronk!".format(member.mention))
			yield from respond(message, "/skronk {}".format(message.author.mention))
			return

	# Is the author trying to skronk himself?
	if member == message.author:
		yield from respond(message, "You can't skronk yourself {}... let me help you with that.".format(member.mention))
		yield from respond(message, "/skronk {}".format(member.mention))
		return

	# Are they trying to skronk the skronker???
	for role in client.user.roles:
		if role == skronk:
			yield from respond(message, "You tryna skronk me???")
			yield from respond(message, "/skronk {}".format(member.mention))
			return
	
	# Okay, let's do the actual skronking
	skronks[member.id] += 1
	yield from client.add_roles(member, skronk)
	yield from respond(message, "{} got SKRONK'D!!!!".format(member.mention))
	yield from remove_skronk(member, message)

@asyncio.coroutine
def remove_skronk(member, message, silent=False, wait=True):
	'''Removes @member form skronk'''
	if wait:
		yield from asyncio.sleep(settings['skronk_timeout'])
	logger.info("Attempting to deskronk {}".format(get_discriminating_name(member)))

	skronk = get_skronk_role(message.server)
	if skronk != None and skronk in member.roles:
		yield from client.remove_roles(member, skronk)
		if not silent:
			yield from respond(message, "You're out of skronk {}!".format(member.mention))

@asyncio.coroutine
def clear_skronks(message, force=False):
	'''Clears all skronks. If this is not a forced clear, it will not happen if the author is skronked''' 
	role = get_skronk_role(message.server)
	if role in message.author.roles and not (force and privileged(message.author)):
		yield from respond(message, "You can't get out of this that easily..")
		return

	skronked = members_of_role(message.server, role)
	for member in skronked:
		yield from remove_skronk(member, message, True, False)

def members_of_role(server, role):
	'''Returns an array of all members for the given role in the given server'''
	ret = []
	for member in server.members:
		if role in member.roles:
			ret.append(member)
	return ret		

def get_skronk_role(server):
	'''Finds the role named SKRONK'D'''
	for role in server.roles:
		if role.name.lower() == SKRONKED.lower():
			return role
	logger.info("Did not find role named {}".format(SKRONKED))
	return None

def get_admin_list(server):
	'''Gets a string containing the list of bot admins'''
	admin_str = 'listens to the following trainers:\n'
	for user in admin_users:
		admin = server.get_member_named(user)
		if admin != None:
			admin_str += ' -' + admin.mention + '\n'
	return admin_str

def get_vote_leaderboards(server, requester):
	'''Returns a string of the current vote leaderboard'''
	server_leaders = []
	cur_votes, start = get_current_votes()
	if(cur_votes == None):
		return 'No one in {} has recieved any votes!'.format(server.name)

	for user_name in cur_votes:
		member = server.get_member_named(user_name)
		if member != None:
			server_leaders.append((member, cur_votes[user_name]))

	if len(server_leaders) == 0:
		return 'No one in {} has recieved any votes!'.format(server.name)

	sorted_ch_lead = sorted(server_leaders, key=lambda tup: tup[1], reverse=True)

	leaderboard_str = '\n \nLeaderboard for week of {}\n{} is in the lead!\nVotes close on {}```'.format(start, sorted_ch_lead[0][0].mention, date_to_string(string_to_date(start) + timedelta(7)))
	for tup in sorted_ch_lead:
		leaderboard_str += '{}: {}'.format(get_user_name(tup[0]), tup[1])
		if requester.name == tup[0].name:
			leaderboard_str +='    <-- It\'s you!\n'
		else:
			leaderboard_str +='\n'
	leaderboard_str +='```'
	return leaderboard_str

def get_vote_history(server, requestor):
	'''Returns a string of all the winners of each recorded voting session'''
	leaders = []

	for date in votes:
		if(len(votes[date]) > 0):
			sorted_users = sorted(votes[date], key=lambda tup: tup[1], reverse=False)			
			idx = 0
			top_score = votes[date][sorted_users[idx]]
			tup = [sorted_users[idx], votes[date][sorted_users[idx]]]
			
			while(tup[1] == top_score):
				temp = server.get_member_named(str(tup[0]))
				if(temp != None):
					leaders.append([date, temp, tup[1]])
				idx = idx + 1
				if(len(sorted_users) > idx ):
					tup = [sorted_users[idx], votes[date][sorted_users[idx]]]
				else:
					break

	history_str = 'All-time voting history:```'
	current_date = None

	if(len(leaders) == 0):
		history_str = "This server has no historical winners for voting..."
	else:
		leaders = sorted(leaders, key=lambda tup: datetime.strptime(tup[0], '%Y-%m-%d'))
		for tup in leaders:
			if(tup[0] != current_date):
				current_date = tup[0]
				history_str += '\n{} - {}: {}'.format(tup[0], get_user_name(tup[1]), tup[2])
			else:
				history_str += '\n              {}: {}'.format(get_user_name(tup[1]), tup[2])

	return history_str + '```'

def get_user_name(user):
	'''Gets a pretty string of a user's name and nickname or just name, if there is no nickname'''
	if(user.nick != None):
		return user.name + ' (' + user.nick + ')'
	else:
		return user.name

def get_current_votes():
	'''Get the votes map for the current session'''
	now = datetime.now().date()
	for start in votes:
		if(now - string_to_date(start) < timedelta(7)):
			return votes[start], start
	return None, None

def date_to_string(date):
	'''Turn a date object into a string formatted the way we want (YYYY-mm-dd)'''
	return date.strftime('%Y-%m-%d')

def string_to_date(string):
	'''Turn a string in YYYY-mm-dd into a date object'''
	return datetime.strptime(string, '%Y-%m-%d').date()

def can_message(server, channel):
	'''True if the bot is authorized and unmuted for the channel, False otherwise'''
	return authorized(server, channel) and not muted(server, channel)

def privileged(user):
	'''True if this user is a bot admin, False otherwise'''
	return get_discriminating_name(user) in admin_users

def get_discriminating_name(user):
	'''Returns a string of the form <Username>#<USERDISCRIMINATOR>'''
	return '{}#{}'.format(user.name, user.discriminator)

def authorized(server, channel):
	'''True if the bot is authorized in this channel'''
	if server.id in authorized_servers:
		return channel.id in authorized_channels[server.id]
	return False

def muted(server, channel):
	'''True if the bot is muted in this channel'''
	if server.id in muted_channels:
		return channel.id in muted_channels[server.id]
	return False

def mute(server, channel):
	'''Adds the channel to the muted list'''
	if server.id in muted_channels:
		if channel.id not in muted_channels[server.id]:
			muted_channels[server.id].append(channel.id)
	else:
		muted_channels[server.id] = [channel.id]

def unmute(server, channel):
	'''Removes the channel from the muted list'''
	if server.id in muted_channels:
		if channel.id in muted_channels[server.id]:
			muted_channels[server.id].remove(channel.id)

def get_date():
	'''Returns a string of the current date in mm-dd-YYYY'''
	return datetime.fromtimestamp(time.time()).strftime('%m-%d-%Y')        

def generate_koffing(server):
	'''Returns a string of a happy koffing'''
	koffing_emoji = get_koffing_emoji(server)
	koffing_str = None
	response = None

	if koffing_emoji != None:
		num_koffs = randint(2,5)
		koffing_str = str(koffing_emoji)
		response = num_koffs*koffing_str + ' ' + 'Koff' + randint(1,5)*'i' + 'ng' + randint(1,5)*'!' + num_koffs*koffing_str
	else:
		response = 'Koff' + randint(1,5)*'i' + 'ng' + randint(1,5)*'!'
	return response, koffing_emoji

def get_koffing_emoji(server):
	'''Returns the koffing emoji if this server has one, None otherwise'''
	koffing_emoji = None
	for emoji in server.emojis:
		if emoji.name == 'koffing':
			koffing_emoji = emoji
	return koffing_emoji

def save_all(silent=False):
	'''Perform all saves'''
	if not silent:
		logger.info('Saving to disk...')
	save_config(True)
	save_feature_toggle(True)
	save_votes(True)
	save_skronk(True)

def save_config(silent=False):
	'''Save the configuration file'''
	contents = {'authorized_channels': authorized_channels, 'authorized_servers': authorized_servers, 'muted_channels': muted_channels, 'admin_users': admin_users, 'game': game_str, 'skronk_timeout': settings['skronk_timeout']}
	if not silent:
		logger.info('Writing settings to disk...')
	save_file(CONFIG_FILE_PATH, contents)

def save_feature_toggle(silent=False):
	'''Save feature toggle map'''
	if not silent:
		logger.info("Writing features to disk...")
	save_file(FEATURE_FILE_PATH, enabled)

def save_votes(silent=False):
	'''Save vote map'''
	if not silent:
		logger.info('Writing votes to disk...')
	save_file(VOTE_FILE_PATH, votes)

def save_skronk(silent=False):
	'''Save skronk list'''
	if not silent:
		logger.info('Saving skronk...')
	save_file(SKRONK_FILE_PATH, skronks)

def save_file(name, obj):
	'''Save the given data to the given file'''
	file = open(name, 'w')
	json_str = json.dumps(obj, sort_keys=True, indent=4)
	file.write(json_str)
	file.close()

logger.info("Starting client with token %s" % TOKEN)
client.loop.create_task(timed_save())
client.run(TOKEN)