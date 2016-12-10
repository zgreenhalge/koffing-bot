import discord
import asyncio
import sys
import datetime
import time
import logging
from random import randint

# OOOUGH (219600948111212544)
# Watchpoint: Dorado (205773751206281216)
# Discord API (81384788765712384)
# Mapleworld Here we Come (215242452284604417)
# Discord is cool kids (182282826010460160)
# Bot Testing (256173272637374464)
# Dan (245295076865998869)

LOG_FORMAT = '[%(asctime)-15s] [%(levelname)s] - %(message)s'
token = 'MjU2MjIyMjU4NjQ3OTI0NzM3.CypBIw.c3RDGrECBWYVwV77aN_2o0j8BkU'
FEATURE_LIST = '```Current feature list (*=requires privilege):\n -responds in text channels!\n -responds in voice channels (NOT IMPLEMENTED)\n -roll call (NOT IMPLEMENTED)\n -song of the day (NOT IMPLEMENTED)\n -elo lookup [Overwatch] (NOT IMPLEMENTED) \n -elo lookup [LoL] (NOT IMPLEMENTED) \n -mute```'
HELP = 'Koffing~~ I will respond any time my name is called!```\nCommands (*=requires privilege):\n !koffing help\n !koffing features\n*!koffing mute\n*!koffing unmute```'
start_messages = ["Koffing-bot, go~!", "Get 'em Koffing-bot~!"]
dev = True
#--------------------------------------------------------------------
client = discord.Client()

#Logging set up
date = datetime.datetime.fromtimestamp(time.time()).strftime('%m-%d-%Y')
logging.basicConfig(format=LOG_FORMAT, level=logging.INFO)
logger = logging.getLogger(__name__)
fh = logging.FileHandler("LOG_" + date + ".txt")
fh.setLevel(logging.DEBUG)
fh.setFormatter(logging.Formatter(LOG_FORMAT))
logger.addHandler(fh)

#Control lists

authorized_servers = ['256173272637374464'] #Bot Testing only
authorized_channels_testing = ['test']
authorized_channels_dan = ['dan_lounge']

authorized_channels = {'256173272637374464': authorized_channels_testing, '245295076865998869': authorized_channels_dan}

muted_channels = {}

admin_users = ['Grachary']
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
                if channel.type==discord.ChannelType.text:
                    if authorized(server, channel):
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
    if(content.startswith('!koffing ')):
        content = content.replace('!koffing ', '', 1)
        if content.startswith('test') and not muted(server, channel):
            yield from client.send_message(channel, 'Okay {}, relax...'.format(author.mention))

        if content.startswith('help') and not muted(server, message):
            yield from client.send_message(channel, HELP)        

        if content.startswith('feature') and not muted(server, channel):
            yield from client.send_message(channel, FEATURE_LIST)

        if content.startswith('mute') and privileged(author.name):
            if not muted(server, channel):
                yield from client.send_message(channel, "Koffing...")
                mute(server, channel)

        if content.startswith('unmute') and privileged(author.name):
            if muted(server, channel):
                response, emoji = generate_koffing(server)
                yield from client.send_message(channel, response)
                unmute(server, channel)

        elif content.startswith('return') and privileged(author.name):
            yield from shutdown_message()
            yield from client.logout()
    else:
        yield from check_for_koffing(message)

@asyncio.coroutine
def shutdown_message():
    for server in client.servers:
        for channel in server.channels:
            if channel.type==discord.ChannelType.text and can_message(server, channel):
                logger.info('Alerting %s::%s to bot shutdown', server.name, channel.name)
                yield from client.send_message(channel, 'Koffing-bot is going back to its pokeball~!')              

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

def privileged(name):
    return name in admin_users

def authorized(server, channel):
    if server.id in authorized_servers:
        return channel.name in authorized_channels[server.id]
    return False

def muted(server, channel):
    if server.id in muted_channels:
        return channel.id in muted_channels[server.id]
    return False

def mute(server, channel):
    if server.id in muted_channels:
        if channel.id not in muted_channels[server.id]:
            muted_channels[server.id].append(channel.id)
    else:
        muted_channels[server.id] = [channel.id]

def unmute(server, channel):
    if server.id in muted_channels:
        if channel.id in muted_channels[server.id]:
            muted_channels[server.id].remove(channel.id)

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

client.run(token)