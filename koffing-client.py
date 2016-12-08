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

LOG_FORMAT = '[%(asctime)-15s] %(message)s'
token = 'MjU2MjIyMjU4NjQ3OTI0NzM3.CypBIw.c3RDGrECBWYVwV77aN_2o0j8BkU'
authorized_channels = ['256173272637374464']
start_messages = ["Koffing-bot, go~!", "Get 'em Koffing-bot~!"]
dev = True
#--------------------------------------------------------------------

client = discord.Client()
date = datetime.datetime.fromtimestamp(time.time()).strftime('%m-%d-%Y')
logging.basicConfig(filename="LOG_" + date + ".txt", format=LOG_FORMAT, level=logging.INFO)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

#--------------------------------------------------------------------

@client.event
@asyncio.coroutine
def on_ready():
    logger.debug('Logged in as %s - %s', client.user.name, client.user.id)
    # print('Logged in as {} ({}) - {}'.format(get_time_str(), client.user.name, client.user.display_name, client.user.id))
    

    # if dev==True:
    #     for server in client.servers:
    #         print('{} ({})'.format(server.name, server.id))
    #     return

    for server in client.servers:
        if server.id in authorized_channels:
            for channel in server.channels:
                if channel.type==discord.ChannelType.text:
                    logger.info('Alerting %s::%s to bot presence', server.name, channel.name)
                    # print('{}  Alerting {}::{} to bot presence'.format(get_time_str(), server.name, channel.name))
                    yield from client.send_message(channel, start_messages[randint(0, len(start_messages)-1)])
                

@client.event
@asyncio.coroutine
def on_message(message):
    if message.server.id not in authorized_channels:
        return
    if message.author.id==client.user.id:
        return
    logger.info('Recieved message from "%s" (%s) in %s::%s', message.author.display_name, message.author.name, message.server.name, message.channel.name)
    # print('{} Recieved message from "{}" ({}) in {}::{}'.format(get_time_str(), message.author.display_name, message.author.name, message.server.name, message.channel.name))


    if message.content.startswith('!test'):
        yield from client.send_message(message.channel, 'Okay {}, relax...'.format(message.author.mention))

    elif message.content.startswith('!koffing'):
        yield from asyncio.sleep(randint(0,5))
        logger.info('     Responding to "%s" (%s) in %s::%s', message.author.display_name, message.author.name, message.server.name, message.channel.name)
        # print('{}   Responding to "{}" ({}) in {}'.format(get_time_str(), message.author.display_name, message.author.name, message.channel.name))
        yield from client.send_message(message.channel, 'Koffing!!')

    elif message.content.startswith('!kill'):
        yield from shutdown_message()
        yield from client.logout()

@asyncio.coroutine
def shutdown_message():
    for server in client.servers:
        if server.id in authorized_channels:
            for channel in server.channels:
                if channel.type==discord.ChannelType.text:
                    logger.info('Alerting %s to bot shutdown', channel.name)
                    # print('{}  Alerting {} to bot shutdown'.format(get_time_str(), channel.name))
                    yield from client.send_message(channel, 'Koffing-bot is going back to its pokeball~!')              

client.run(token)