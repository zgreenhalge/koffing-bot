import discord
import asyncio
import sys
import datetime
import time
import logging
import json
from random import randint

# Bot Testing (256173272637374464)
# Dan (245295076865998869)

LOG_FORMAT = '[%(asctime)-15s] [%(levelname)s] - %(message)s'
TOKEN = 'MjU2MjIyMjU4NjQ3OTI0NzM3.CypBIw.c3RDGrECBWYVwV77aN_2o0j8BkU'
FEATURE_LIST = '```Current feature list (*=requires privilege):\n -responds in text channels!\n -responds in voice channels (PLANNED)\n -roll call (PLANNED)\n -song of the day (PLANNED)\n -elo lookup [Overwatch] (PLANNED) \n -elo lookup [LoL] (PLANNED) \n -mute\n -vote (PLANNED)```'
HELP = 'Koffing~~ I will respond any time my name is called!```\nCommands (*=requires privilege):\n /koffing help\n /koffing features\n*/koffing mute\n*/koffing unmute```'
CONFIG = 'koffing.cfg'
start_messages = ["Koffing-bot, go~!", "Get 'em Koffing-bot~!"]
dev = True
#--------------------------------------------------------------------
#Logging set up
date = datetime.datetime.fromtimestamp(time.time()).strftime('%m-%d-%Y')
logging.basicConfig(format=LOG_FORMAT, level=logging.INFO)
logger = logging.getLogger(__name__)
fh = logging.FileHandler("LOG_" + date + ".txt")
fh.setLevel(logging.DEBUG)
fh.setFormatter(logging.Formatter(LOG_FORMAT))
logger.addHandler(fh)

#Control lists
settings = json.load(open(CONFIG))
authorized_servers = settings['authorized_servers']
authorized_channels = settings['authorized_channels']
muted_channels = settings['muted_channels']
admin_users = settings['admin_users']

client = discord.Client()
#--------------------------------------------------------------------

@client.event
@asyncio.coroutine
def on_ready():
    
    logger.info('\n-----------------\nLogged in as %s - %s\n-----------------', client.user.name, client.user.id)    
    if dev==True:
        logger.info('Member of the following servers:')
        for server in client.servers:
            logger.info(' %s (%s)', server.name, server.id)

    for server in client.servers:
        if server.id in authorized_servers:
            for channel in server.channels:
                if channel.type==discord.ChannelType.text and can_message(server, channel):
                    logger.info('Alerting %s::%s to bot presence', server.name, channel.name)
                    yield from client.send_message(channel, start_messages[randint(0, len(start_messages)-1)])
                

@client.event
@asyncio.coroutine
def on_message(message):
    logger.debug('Recieved message from "%s" (%s) in %s::%s', message.author.display_name, message.author.name, message.server.name, message.channel.name)
    
    if not authorized(message.server, message.channel):
        return
    if message.author.id==client.user.id:
        return

    server = message.server
    channel = message.channel
    content = message.content
    author = message.author

    if(content.startswith('/koffing ')):
        content = content.replace('/koffing ', '', 1) #remove the first '/koffing' from the string for easier parsing of command

        elif content.startswith('help') and not muted(server, message):
            yield from client.send_message(channel, HELP)        

        elif content.startswith('feature') and not muted(server, channel):
            yield from client.send_message(channel, FEATURE_LIST)

        elif content.startswith('admin'):
            content = content.replace('admin ', '', 1)
            if not privileged(author) and not muted(server, channel):
                yield from client.send_message(channel, "I'm afraid you can't do that {}".format(author.mention))
            elif content.startswith('list') and not muted(server, channel):
                yield from client.send_message(channel, get_admin_list())
            elif content != '' and content not in admin_users:
                admin_users.append(content)

        elif content.startswith('mute'):
            content = content.replace('mute ', '', 1)
            if not privileged(author) and not muted(server, channel):
                yield from client.send_message(channel, "I'm afraid you can't do that {}".format(author.mention))
            else:
                mute(server, channel)
                if not muted(server, channel):
                    yield from client.send_message(channel, "Koffing...")

        elif content.startswith('unmute'):
            if not privileged(author) and not muted(server, channel):
                yield from client.send_message(channel, "I'm afraid you can't do that {}".format(author.mention))
            else:
                if muted(server, channel):
                    response, emoji = generate_koffing(server)
                    yield from client.send_message(channel, response)
                unmute(server, channel)

        elif content.startswith('return') and privileged(author):
            yield from shutdown_message()
            yield from client.logout()

        elif not muted(server, channel):
            yield from client.send_message(channel, "Koff koff~ \nInvalid command, please use /koffing help for usage")
    else:
        yield from check_for_koffing(message)

@asyncio.coroutine
def shutdown_message():
    save_config()
    for server in client.servers:
        for channel in server.channels:
            if channel.type==discord.ChannelType.text and can_message(server, channel):
                logger.info('Alerting %s::%s to bot shutdown', server.name, channel.name)
                yield from client.send_message(channel, 'Koffing-bot is going back to its pokeball~!')              

def save_config():
    logger.info('Writing settings to file...')
    file = open(CONFIG, 'w')
    json_str = json.dumps({'authorized_channels': authorized_channels, 'authorized_servers': authorized_servers, 'muted_channels': muted_channels, 'admin_users': admin_users})
    file.write(json_str)
    file.close()

def get_admin_list():
    admin_str = 'Trainers that I listen to:\n'
    for user in admin_users:
        admin_str += ' -' + user + '\n'
    return admin_str

@asyncio.coroutine
def check_for_koffing(message):
    if 'koffing' in message.content:
        logger.debug('  Responding to "%s" (%s) in %s::%s', message.author.display_name, message.author.name, message.server.name, message.channel.name)
        
        response, emoji = generate_koffing(message.server)
        if can_message(message.server, message.channel):
            yield from client.send_message(message.channel, response)
            yield from client.add_reaction(message, emoji)

        # need to figure out ffmpeg before this will work
        if message.author.voice_channel != None:
            logger.debug('Attempting to play in voice channel %s', message.author.voice_channel.name)
            voice = yield from client.join_voice_channel(message.author.voice_channel)
            player = voice.create_ffmpeg_player('koffing.mp3')
            player.start()

def can_message(server, channel):
    return authorized(server, channel) and not muted(server, channel)

def privileged(user):
    return user.mention in admin_users

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

def generate_koffing(server):
    koffing_emoji = None
    koffing_str = None
    for emoji in server.emojis:
        if emoji.name == 'koffing':
            koffing_emoji = emoji

    if koffing_emoji != None:
        num_koffs = randint(2,5)
        koffing_str = str(koffing_emoji)
        response = num_koffs*koffing_str + ' ' + 'Koff' + randint(1,5)*'i' + 'ng' + randint(1,5)*'!' + num_koffs*koffing_str
    else:
        reponse = 'Koff' + randint(1,5)*'i' + 'ng' + randint(1,5)*'!'
    return response, koffing_emoji

client.run(TOKEN)