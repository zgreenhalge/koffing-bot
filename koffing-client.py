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
FEATURE_LIST = 'Current feature list:\n -responds in text channels! (DONE)\n -responds in voice channels (NOT IMPLEMENTED)\n -roll call (NOT IMPLEMENTED)\n -song of the day (NOT IMPLEMENTED)'
authorized_servers = ['256173272637374464'] #Bot Testing only
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

#--------------------------------------------------------------------

@client.event
@asyncio.coroutine
def on_ready():
    logger.debug('Logged in as %s - %s', client.user.name, client.user.id)    

    if dev==True:
        logger.info('Member of the following servers:')
        for server in client.servers:
            logger.info(' %s (%s)', server.name, server.id)

    for server in client.servers:
        if server.id in authorized_servers:
            for channel in server.channels:
                if channel.type==discord.ChannelType.text:
                    logger.info('Alerting %s::%s to bot presence', server.name, channel.name)
                    yield from client.send_message(channel, start_messages[randint(0, len(start_messages)-1)])
                

@client.event
@asyncio.coroutine
def on_message(message):
    if message.server.id == '236606365391519744':
        logger.info('%s: %s', message.author.name, message.content)
        return
    if message.server.id not in authorized_servers:
        return
    if message.author.id==client.user.id:
        return

    logger.debug('Recieved message from "%s" (%s) in %s::%s', message.author.display_name, message.author.name, message.server.name, message.channel.name)
    yield from check_for_koffing(message)

    if message.content.startswith('!test'):
        yield from client.send_message(message.channel, 'Okay {}, relax...'.format(message.author.mention))

    if message.content.startswith('!help'):
        yield from client.send_message(message.channel, "I'll get around to this later...")        

    if message.content.startswith('!feature'):
        yield from client.send_message(message.channel, FEATURE_LIST)

    elif message.content.startswith('!kill'):
        yield from shutdown_message()
        yield from client.logout()

@asyncio.coroutine
def shutdown_message():
    for server in client.servers:
        if server.id in authorized_servers:
            for channel in server.channels:
                if channel.type==discord.ChannelType.text:
                    logger.info('Alerting %s to bot shutdown', channel.name)
                    yield from client.send_message(channel, 'Koffing-bot is going back to its pokeball~!')              

@asyncio.coroutine
def check_for_koffing(message):
    if message.content.startswith('!koffing') or 'koffing' in message.content:
        logger.debug('  Responding to "%s" (%s) in %s::%s', message.author.display_name, message.author.name, message.server.name, message.channel.name)
        
        koffing_emoji = None
        koffing_str = None
        for emoji in message.server.emojis:
            if emoji.name == 'koffing':
                koffing_emoji = emoji

        koffing_str = str(koffing_emoji)
        response = randint(1,3)*koffing_str + ' ' + 'Koff' + randint(1,5)*'i' + 'ng!!' + randint(1,3)*koffing_str
        yield from client.send_message(message.channel, response)
        yield from client.add_reaction(message, koffing_emoji)

        if message.author.voice_channel != None:
            logger.debug('Attempting to play in voice channel %s', message.author.voice_channel.name)
            voice = yield from client.join_voice_channel(message.author.voice_channel)
            player = voice.create_ffmpeg_player('koffing.mp3')
            player.start()


client.run(token)