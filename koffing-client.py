import discord
import asyncio
from random import randint

dan_id = '245295076865998869'
start_messages = ["Koffing-bot, go!", "Get 'em Koffing-bot!"]

client = discord.Client()

@client.event
@asyncio.coroutine
def on_ready():
    print('Logged in as')
    print('{} ({}) - {}'.format(client.user.name, client.user.display_name, client.user.id))
    print('------')
    for server in client.servers:
        if server.id==dan_id:
            for channel in server.channels:
                if channel.type==discord.ChannelType.text:
                    print('  Alerting {} to bot presence'.format(channel.name))
                    yield from client.send_message(channel, start_messages[randint(0, len(start_messages)-1)])
                

@client.event
@asyncio.coroutine
def on_message(message):
    if message.server.id!=dan_id:
        return
    print('Recieved message from {} ({}) in {}::{}'.format(message.author.display_name, message.author.name, message.server.name, message.channel.name))
    if message.author.id==client.user.id:
        return
    if message.content.startswith('!test'):
        yield from client.send_message(message.channel, 'Okay @{}, relax...'.format(message.author.name))

    elif message.content.startswith('!koffing'):
        yield from asyncio.sleep(randint(0,5))
        print("  Responding to {} ({}) in {}".format(message.author.display_name, message.author.name, message.channel.name))
        yield from client.send_message(message.channel, 'Koffing!!')

    elif message.content.startswith('!return'):
        shutdown_message()
        yield from client.logout()
        sys.exit()

def shutdown_message():
    for server in client.servers:
        if server.id==dan_id:
            for channel in server.channels:
                if channel.type==discord.ChannelType.text:
                    print('  Alerting {} to bot shutdown'.format(channel.name))
                    yield from client.send_message(channel.id, 'Koffing-bot is going back to its pokeball!')


# client.run('token')
client.run('zgreenhalge@gmail.com', 'seraphim')