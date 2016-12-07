import discord
import asyncio
import sys
import datetime
import time
from random import randint

dan_id = '245295076865998869'
start_messages = ["Koffing-bot, go~!", "Get 'em Koffing-bot~!"]
dev = True

client = discord.Client()

@client.event
@asyncio.coroutine
def on_ready():
    print('{} Logged in as {} ({}) - {}'.format(get_time_str(), client.user.name, client.user.display_name, client.user.id))
    if dev==True:
        return
    for server in client.servers:
        if server.id==dan_id:
            for channel in server.channels:
                if channel.type==discord.ChannelType.text:
                    print('{}  Alerting {} to bot presence'.format(get_time_str(), channel.name))
                    yield from client.send_message(channel, start_messages[randint(0, len(start_messages)-1)])
                

@client.event
@asyncio.coroutine
def on_message(message):
    if message.server.id!=dan_id:
        return
    print('{} Recieved message from "{}" ({}) in {}::{}'.format(get_time_str(), message.author.display_name, message.author.name, message.server.name, message.channel.name))

    if message.author.id==client.user.id and dev==False:
        return
    if message.content.startswith('!test'):
        yield from client.send_message(message.channel, 'Okay {}, relax...'.format(message.author.mention))

    elif message.content.startswith('!koffing'):
        yield from asyncio.sleep(randint(0,5))
        print('{}   Responding to "{}" ({}) in {}'.format(get_time_str(), message.author.display_name, message.author.name, message.channel.name))
        yield from client.send_message(message.channel, 'Koffing!!')

    elif message.content.startswith('!kill'):
        yield from shutdown_message()
        yield from client.logout()

@asyncio.coroutine
def shutdown_message():
    for server in client.servers:
        if server.id==dan_id:
            for channel in server.channels:
                if channel.type==discord.ChannelType.text:
                    print('{}  Alerting {} to bot shutdown'.format(get_time_str(), channel.name))
                    yield from client.send_message(channel, 'Koffing-bot is going back to its pokeball~!')

def get_time_str():
    return '[{}]'.format(datetime.datetime.fromtimestamp(time.time()).strftime('%m-%d-%Y %H:%M:%S'))

# client.run('token')
client.run('zgreenhalge@gmail.com', 'seraphim')