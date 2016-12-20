import discord
import asyncio
import sys
import time
import logging
import json
import operator
from random import randint
from datetime import datetime
from datetime import timedelta

# Bot Testing (256173272637374464)
# Dan (245295076865998869)

LOG_FORMAT = '[%(asctime)-15s] [%(levelname)s] - %(message)s'
TOKEN = 'MjU2MjIyMjU4NjQ3OTI0NzM3.CzUM4A.gSmNOYmh08W_EbF-d9LSPLXo2HY'
FEATURE_LIST = '```Current feature list (*=requires privilege):\n -responds in text channels!\n -responds in voice channels (PLANNED)\n -roll call (PLANNED)\n -song of the day pinning!\n -elo lookup [Overwatch] (PLANNED) \n -elo lookup [LoL] (PLANNED) \n -mute\n -vote!```'
HELP = 'Koffing~~ I will respond any time my name is called!```\nCommands (*=requires privilege):\n /koffing help\n /koffing features\n*/koffing mute\n*/koffing unmute\n*/koffing admin [list] [remove (@user) [@user]] [add (@user) [@user]]\n*/koffing play [name]\n*/koffing return```'
CONFIG_FILE_NAME = 'koffing.cfg'
FEATURE_FILE_NAME = "feature_toggle.cfg"
VOTE_FILE_NAME = 'vote_count'
start_messages = ["Koffing-bot, go~!", "Get 'em Koffing-bot~!"]
dev = True
#--------------------------------------------------------------------
#Logging set up
date = datetime.fromtimestamp(time.time()).strftime('%m-%d-%Y')
logging.basicConfig(format=LOG_FORMAT, level=logging.INFO)
logger = logging.getLogger(__name__)
fh = logging.FileHandler("LOG_" + date + ".txt")
fh.setLevel(logging.DEBUG)
fh.setFormatter(logging.Formatter(LOG_FORMAT))
logger.addHandler(fh)
#--------------------------------------------------------------------
#Control lists
settings = json.load(open(CONFIG_FILE_NAME))
authorized_servers = settings['authorized_servers']
authorized_channels = settings['authorized_channels']
muted_channels = settings['muted_channels']
admin_users = settings['admin_users']
game_str = settings['game']
enabled = json.load(open(FEATURE_FILE_NAME))
#--------------------------------------------------------------------
votes = json.load(open(VOTE_FILE_NAME))

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
				if channel.type==discord.ChannelType.text and can_message(server, channel):
					logger.info('Alerting %s::%s to bot presence', server.name, channel.name)
					yield from client.send_message(channel, start_messages[randint(0, len(start_messages)-1)])
				

@client.event
@asyncio.coroutine
def on_message(message):
	if not authorized(message.server, message.channel):
		return
	if message.author.id==client.user.id:
		return

	logger.info('Recieved message from "%s" (%s) in %s::%s', message.author.display_name, get_discriminating_name(message.author), message.server.name, message.channel.name)

	global game_str
	server = message.server
	channel = message.channel
	content = (message.content + '.')[:-1].lower()
	author = message.author

	if(content.startswith('/koffing ')):
		content = content.replace('/koffing', '', 1).lstrip().rstrip()

		if content.startswith('help'):
			yield from respond(message, HELP)        

		elif content.startswith('feature'):
			if not enabled['features']:
				yield from respond(message, 'The planned feature list is not enabled')
			else:
				yield from respond(message, FEATURE_LIST)

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

		elif content.startswith('mute'):
			if not privileged(author):
				yield from respond(message, "I'm afraid you can't do that {}".format(author.mention))
			elif not enabled["mute"]:
				yield from respond(message, 'Mute feature is disabled')
			else:
				yield from respond(message, "Koffing...")
				mute(server, channel)

		elif content.startswith('unmute'):
			if not privileged(author):
				yield from respond(message, "I'm afraid you can't do that {}".format(author.mention))
			elif not enabled["mute"]:
				yield from respond(message, 'Mute feature is disabled')
			else:
				if muted(server, channel):
					response, emoji = generate_koffing(server)
					logger.info('  Responding to "%s" (%s) in %s::%s', author.display_name, get_discriminating_name(author), server.name, channel.name)
					yield from client.send_message(channel, response)
				unmute(server, channel)

		elif content.startswith('game') or content.startswith('play'):
			if not privileged(author):
				yield from respond(message, "I'm afraid you can't do that {}".format(author.mention))
			elif not enabled["game"]:
				yield from respond(message, 'Game feature is disabled')
			else:
				game_str = message.content[13:].lstrip().rstrip()
				logger.info("  Setting bot to playing '{}'".format(game_str))
				yield from client.change_presence(game=discord.Game(name=game_str))

		elif content.startswith('return'):
			if not privileged(author):
				yield from respond(message, "I'm afraid you can't do that {}".format(author.mention))
			else:
				yield from shutdown_message()
				yield from client.logout()

		else:
			yield from respond(message, "Skronk!".format(author.mention))

	elif content.startswith('#sotd'):
		if not enabled['sotd_pin']:
			logger.info("  sotd_pin is not enabled")
			return
		# Quiet skip this, since the user may not be actively asking for it
		logger.info('  Pinning #SotD')
		yield from pin(message)

	elif content.startswith('/vote'):
		if not enabled['voting']:
			yield from respond(message, "I'm afraid you can't do that {}".format(author.mention))
		else:
			content = content.replace('/vote', '', 1).lstrip().rstrip()
			if content.startswith('leaderboard') or content.startswith('boards') or content.startswith('leaders'):
				yield from respond(message, get_vote_leaderboards(server, author))
			else:
				yield from place_vote(message)

	else:
		yield from check_for_koffing(message)

@asyncio.coroutine
def shutdown_message():
	save_all()
	for server in client.servers:
		for channel in server.channels:
			if channel.type==discord.ChannelType.text and can_message(server, channel):
				logger.info('Alerting %s::%s to bot shutdown', server.name, channel.name)
				yield from client.send_message(channel, 'Koffing-bot is going back to its pokeball~!')              

@asyncio.coroutine
def check_for_koffing(message):
	if 'koffing' in message.content.lower() or client.user.mentioned_in(message):

		if can_message(message.server, message.channel) and enabled["text_response"]:
			# Quiet skip this, since that's the point of disabled text response
			yield from client.send_typing(message.channel)
			response, emoji = generate_koffing(message.server)
			asyncio.sleep(randint(0,3))
			yield from respond(message, response)
			yield from client.add_reaction(message, emoji)

		return #RETURN HERE TO STOP VOICE FROM HAPENING BEFORE IT WORKS
		# need to figure out ffmpeg before this will work
		if message.author.voice_channel != None and enabled["voice_response"]:
			logger.debug('Attempting to play in voice channel %s', message.author.voice_channel.name)
			voice = voice_client_int(message.server)
			if voice == None or voice.channel != message.author.voice_channel:
				voice = yield from client.join_voice_channel(message.author.voice_channel)
			player = voice.create_ffmpeg_player('koffing.mp3')
			player.start()

@asyncio.coroutine
def add_admin(message):
	users = message.mentions 
	channel = message.channel
	for user in users:
		user_str = get_discriminating_name(user)
		if user_str not in admin_users:
			admin_users.append(user_str)
			yield from respond(message, "Added {} to the admin list.".format(user.mention))

@asyncio.coroutine
def remove_admin(message):
	users = message.mentions
	channel = message.channel
	for user in users:
		user_str = get_discriminating_name(user)
		if user_str in admin_users:
			admin_users.remove(user_str)
			yield from respond(message, "Removed {} from the admin list.".format(user.mention))

@asyncio.coroutine
def respond(message, text):
	if not muted(message.server, message.channel):
		logger.info('  Responding to "%s" (%s) in %s::%s', message.author.display_name, get_discriminating_name(message.author), message.server.name, message.channel.name)
		yield from client.send_message(message.channel, text)

@asyncio.coroutine
def pin(message):
	try:
		emoji = get_koffing_emoji(message.server)
		if emoji != None:
			yield from client.add_reaction(message, emoji)
		yield from client.pin_message(message)
	except NotFound:
		logger.warn('Message or channel has been deleted, pin failed')
	except Forbidden:
		logger.warn('Koffing-bot does not have sufficient permissions to pin in %s::%s'.format(server.name, channel.name))
	except (Error, Exception) as e:
		logger.error('Could not pin message: {}'.format(e))

@asyncio.coroutine
def place_vote(message):
	if len(message.mentions) == 0:
		yield from respond(message, "You need to tag someone to vote for them!")
		return

	member = message.mentions[0]
	name = get_discriminating_name(member)
	
	check = message.content.replace('/vote', '', 1)
	if not check.lstrip().rstrip().startswith(member.mention):
		yield from respond(message, "Skronk!")
		return
	
	if member.id == message.author.id:
		yield from respond(message, "You can't vote for yourself {}....".format(member.mention))

	else:
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
		yield from respond(message, "{}, you just got a vote! Total votes: {}".format(member.mention, cur_votes[name]))

def get_admin_list(server):
	admin_str = 'listens to the following trainers:\n'
	for user in admin_users:
		admin = server.get_member_named(user)
		if admin != None:
			admin_str += ' -' + admin.mention + '\n'
	return admin_str

def get_vote_leaderboards(server, requester):
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
		if tup[0].nick != None:
			leaderboard_str += '{} ({}): {}'.format(tup[0].name, tup[0].nick, tup[1])
		else:
			leaderboard_str += '{}: {}'.format(tup[0].name, tup[1])
		if requester.name == tup[0].name:
			leaderboard_str +='    <-- It\'s you!\n'
		else:
			leaderboard_str +='\n'
	leaderboard_str +='```'
	return leaderboard_str

def get_current_votes():
	now = datetime.now().date()
	for start in votes:
		if(now - string_to_date(start) < timedelta(7)):
			return votes[start], start
	return None, None

def date_to_string(date):
	return date.strftime('%Y-%m-%d')

def string_to_date(string):
	return datetime.strptime(string, '%Y-%m-%d').date()

def can_message(server, channel):
	return authorized(server, channel) and not muted(server, channel)

def privileged(user):
	return get_discriminating_name(user) in admin_users

def get_discriminating_name(user):
	return '{}#{}'.format(user.name, user.discriminator)

def authorized(server, channel):
	if server.id in authorized_servers:
		return channel.name in authorized_channels[server.id]
	return False

def muted(server, channel):
	if server.id in muted_channels:
		return channel.name in muted_channels[server.id]
	return False

def mute(server, channel):
	if server.id in muted_channels:
		if channel.name not in muted_channels[server.id]:
			muted_channels[server.id].append(channel.name)
	else:
		muted_channels[server.id] = [channel.name]

def unmute(server, channel):
	if server.id in muted_channels:
		if channel.name in muted_channels[server.id]:
			muted_channels[server.id].remove(channel.name)

def get_date():
	return datetime.fromtimestamp(time.time()).strftime('%m-%d-%Y')        

def generate_koffing(server):
	koffing_emoji = get_koffing_emoji(server)
	koffing_str = None

	if koffing_emoji != None:
		num_koffs = randint(2,5)
		koffing_str = str(koffing_emoji)
		response = num_koffs*koffing_str + ' ' + 'Koff' + randint(1,5)*'i' + 'ng' + randint(1,5)*'!' + num_koffs*koffing_str
	else:
		reponse = 'Koff' + randint(1,5)*'i' + 'ng' + randint(1,5)*'!'
	return response, koffing_emoji

def get_koffing_emoji(server):
	koffing_emoji = None
	for emoji in server.emojis:
		if emoji.name == 'koffing':
			koffing_emoji = emoji
	return koffing_emoji

def save_all():
	save_config()
	save_feature_toggle()
	save_votes()

def save_config():
	logger.info('Writing settings to disk...')
	file = open(CONFIG_FILE_NAME, 'w')
	json_str = json.dumps({'authorized_channels': authorized_channels, 'authorized_servers': authorized_servers, 'muted_channels': muted_channels, 'admin_users': admin_users, 'game': game_str}, sort_keys=True, indent=4)
	file.write(json_str)
	file.close()

def save_feature_toggle():
	logger.info("Writing features to disk...")
	file = open(FEATURE_FILE_NAME, 'w')
	json_str = json.dumps(enabled, sort_keys=True, indent=4)
	file.write(json_str)
	file.close()

def save_votes():
	logger.info('Writing votes to disk...')
	file = open(VOTE_FILE_NAME, 'w')
	json_str = json.dumps(votes,sort_keys=True, indent=4)
	file.write(json_str)
	file.close()

client.run(TOKEN)
