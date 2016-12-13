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
FEATURE_LIST = '```Current feature list (*=requires privilege):\n -responds in text channels!\n -responds in voice channels (PLANNED)\n -roll call (PLANNED)\n -song of the day (PLANNED)\n -elo lookup [Overwatch] (PLANNED) \n -elo lookup [LoL] (PLANNED) \n -mute\n -vote (PLANNED)\n -blacklist (PLANNED)```'
HELP = 'Koffing~~ I will respond any time my name is called!```\nCommands (*=requires privilege):\n /koffing help\n /koffing features\n*/koffing mute\n*/koffing unmute\n*/koffing admin [list] [remove (@user) [@user]] [add (@user) [@user]]\n*/koffing return```'
CONFIG = 'koffing.cfg'
FEAT_TOGGLE = "feature_toggle.cfg"
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
enabled_features = {"mute": True, "features": True, "text_response": True, "voice_response": False, "sotd_pin": False}
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
    if not authorized(message.server, message.channel):
        return
    if message.author.id==client.user.id:
        return

    logger.info('Recieved message from "%s" (%s) in %s::%s', message.author.display_name, get_discriminating_name(message.author), message.server.name, message.channel.name)

    server = message.server
    channel = message.channel
    content = message.content
    author = message.author

    if(content.startswith('/koffing ')):
        content = content.replace('/koffing ', '', 1) #remove the first '/koffing' from the string for easier parsing of command

        if content.startswith('help') and not muted(server, channel):
            yield from respond(message, HELP)        

        elif content.startswith('feature') and not muted(server, channel):
            yield from respond(message, FEATURE_LIST)

        elif content.startswith('admin'):
            content = content.replace('admin ', '', 1)
            if not privileged(author) and not muted(server, channel):
                yield from respond(message, "I'm afraid you can't do that {}".format(author.mention))
            elif content.startswith('list') and not muted(server, channel):
                yield from respond(message, get_admin_list(server))
            elif (content.startswith('rm') or content.startswith('remove')):
                yield from remove_admin(message)
            elif content.startswith('add'):
                yield from add_admin(message)

        elif content.startswith('mute'):
            content = content.replace('mute ', '', 1)
            if not privileged(author):
                if not muted(server, channel):
                    yield from respond(message, "I'm afraid you can't do that {}".format(author.mention))
            else:
                if not muted(server, channel):
                    yield from respond(message, "Koffing...")
                mute(server, channel)

        elif content.startswith('unmute'):
            if not privileged(author):
                if not muted(server, channel):
                    yield from respond(message, "I'm afraid you can't do that {}".format(author.mention))
            else:
                if muted(server, channel):
                    response, emoji = generate_koffing(server)
                    yield from respond(message, response)
                unmute(server, channel)

        elif content.startswith('return'):
            if not privileged(author):
                if not muted(server, channel):
                    yield from respond(message, "I'm afraid you can't do that {}".format(author.mention))
            else:
                yield from shutdown_message()
                yield from client.logout()

        elif not muted(server, channel):
            yield from respond(message, "Koff koff {}~ \n`Invalid command, please use /koffing help for usage`".format(author.mention))
    elif content.startswith('#SotD'):
        try:
            yield from client.pin_message(message)
        except NotFound:
            logger.warn('Message or channel has been deleted, pin failed')
        except Forbidden:
            logger.warn('Koffing-bot does not have sufficient permissions to pin in %s::%s'.format(server.name, channel.name))
        except (Error, Exception) as e:
            logger.error('Could not pin message: {}'.format(e))
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
    if 'koffing' in message.content or client.user.mentioned_in(message):
        
        if can_message(message.server, message.channel):
            yield from client.send_typing(message.channel)

        response, emoji = generate_koffing(message.server)

        if can_message(message.server, message.channel):
            asyncio.sleep(randint(0,2))
            yield from respond(message, response)
            yield from client.add_reaction(message, emoji)

        return #RETURN HERE TO STOP VOICE FROM HAPENING BEFORE IT WORKS
        # need to figure out ffmpeg before this will work
        if message.author.voice_channel != None:
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
            if not muted(message.server, channel):
                yield from respond(message, "Added {} to the admin list.".format(user.mention))

@asyncio.coroutine
def remove_admin(message):
    users = message.mentions
    channel = message.channel
    for user in users:
        user_str = get_discriminating_name(user)
        if user_str in admin_users:
            admin_users.remove(user_str)
            if not muted(message.server, channel):
                yield from respond(message, "Removed {} from the admin list.".format(user.mention))

@asyncio.coroutine
def respond(message, text):
    logger.info('  Responding to "%s" (%s) in %s::%s', message.author.display_name, get_discriminating_name(message.author), message.server.name, message.channel.name)
    yield from client.send_message(message.channel, text)

def get_admin_list(server):
    admin_str = 'listens to the following trainers:\n'
    for user in admin_users:
        admin = server.get_member_named(user)
        if admin != None:
            admin_str += ' -' + admin.mention + '\n'
    return admin_str

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
    return datetime.datetime.fromtimestamp(time.time()).strftime('%m-%d-%Y')        

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

def save_all():
    save_config()
    save_feature_toggle()

def save_config():
    logger.info('Writing settings to disk...')
    file = open(CONFIG, 'w')
    json_str = json.dumps({'authorized_channels': authorized_channels, 'authorized_servers': authorized_servers, 'muted_channels': muted_channels, 'admin_users': admin_users}, sort_keys=True, indent=4)
    file.write(json_str)
    file.close()

def save_feature_toggle():
    logger.info("Writing features to disk...")
    file = open(FEAT_TOGGLE, 'w')
    json_str = json.dumps(enabled_features)
    file.write(json_str)
    file.close()

client.run(TOKEN)