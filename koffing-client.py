import sys

from features.onmessage.AdminConsole import AdminConsole
from features.onmessage.RemindMe import create_reminder
from util import DateTime, Feature, Client
from util.Feature import start_bkg_feature_tasks, load_pending_tasks, get_feature_list, init_features
from util.Messaging import *
from util.User import *

if len(sys.argv) < 2:
	TOKEN = input('Please enter token: ')
else:
	TOKEN = sys.argv[1].lstrip().rstrip()

START_MESSAGES = ["Koffing-bot, go~!", "Get 'em Koffing-bot~!"]

dev = True


# --------------------------------------------------------------------
# Logging set up

logger = Logging.get_logger()

logger.warning('###############################################')
logger.warning('#-----------------NEW SESSION-----------------#')
logger.warning('#------------------' + DateTime.get_current_date_string() + '-----------------#')
logger.warning('###############################################')
# --------------------------------------------------------------------
# The discord client!

client = discord.Client(intents=discord.Intents.all())

# --------------------------------------------------------------------
# Control lists & task loading
Settings.load_settings()


@client.event
async def on_ready():
	"""
	Called when the client has successfully started up & logged in with our token
	"""
	logger.debug('\n-----------------\nLogged in as {} - {}\n-----------------'.format(client.user.name, client.user.id))
	if dev:
		logger.debug('Member of the following guilds:')
		for guild in client.guilds:
			logger.debug('  {} ({})'.format(guild.name, guild.id))

	# Feature related loading happens once the event loop is initialized
	Feature.client = client
	init_features()
	load_pending_tasks(get_feature_list())
	start_bkg_feature_tasks()

	new_game = discord.Game(Settings.game_str)
	await client.change_presence(activity=new_game)

	await startup_message(client)
	logger.warning('Koffing-bot is up and running!')


@client.event
async def on_message(message):
	"""
	Fires when the client receives a new message. Main starting point for message & command processing
	"""
	if message.channel is None or message.guild is None or not isinstance(message.channel, discord.abc.GuildChannel):
		await on_direct_message(message)
		return

	logger.info('Received message from "%s" (%s) in %s::%s', get_preferred_name(message.author),
				get_discriminating_name(message.author), message.guild.name, message.channel.name)

	if not Channel.authorized(message.guild, message.channel):
		return

	for task in Feature.on_msg_features:
		if task.should_execute(message):
			logger.debug("Executing {}".format(type(task).__name__))
			await task.execute(message)
			return


async def on_direct_message(message):
	"""
	C&C for direct messages, we get forwarded here from on_message()
	"""
	if message.author.id is client.user.id:
		return

	logger.info('Got a DM from %s', get_discriminating_name(message.author))
	content = message.content

	if content.startswith(Settings.cmd_prefix + 'remindme'):
		await create_reminder(message)
	elif content.startswith(Settings.cmd_prefix):
		console = AdminConsole.get_instance(client)
		await console.execute(message)
	else:
		await direct_response(message, '')


# --------------------------------------------------------------------
# Bring koffing to life! Bring him to liiiiiife!!!!
logger.info('Starting client...')
client.run(TOKEN)
logger.info('Client exited successfully. Goodnight~')
sys.exit(Client.exit_value)
