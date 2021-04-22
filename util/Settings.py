import os
from util import LoggingUtils
from util.FileUtils import turn_file_to_json, save_file

CONFIG_FILE_NAME = 'koffing.cfg'
FEATURE_FILE_NAME = "feature_toggle.cfg"
VOTE_FILE_NAME = 'vote_count.txt'
SKRONK_FILE_NAME = 'skronk.txt'

CONFIG_DIR_PATH = os.path.abspath(os.path.join('config'))
CONFIG_FILE_PATH = os.path.join(CONFIG_DIR_PATH, CONFIG_FILE_NAME)
FEATURE_FILE_PATH = os.path.join(CONFIG_DIR_PATH, FEATURE_FILE_NAME)
VOTE_FILE_PATH = os.path.join(CONFIG_DIR_PATH, VOTE_FILE_NAME)
SKRONK_FILE_PATH = os.path.join(CONFIG_DIR_PATH, SKRONK_FILE_NAME)

logger = LoggingUtils.get_logger()


def load_settings():
	global settings, enabled, votes, skronks, authorized_guilds, authorized_channels, muted_channels, admin_users, game_str, SILENT_MODE, SAVE_TIMEOUT, GENTLE_SHUTDOWN

	if not os.path.exists(CONFIG_DIR_PATH):
		logger.info("Creating {}...".format(CONFIG_DIR_PATH))
		os.makedirs(CONFIG_DIR_PATH)

	logger.info("Loading settings...")
	settings = turn_file_to_json(CONFIG_FILE_PATH, False)
	enabled = turn_file_to_json(FEATURE_FILE_PATH, False)
	votes = turn_file_to_json(VOTE_FILE_PATH, False)
	skronks = turn_file_to_json(SKRONK_FILE_PATH, False)

	authorized_guilds = settings['authorized_guilds']
	authorized_channels = settings['authorized_channels']
	muted_channels = settings['muted_channels']
	admin_users = settings['admin_users']
	game_str = settings['game']
	SILENT_MODE = settings['silent_mode']
	SAVE_TIMEOUT = settings['save_timeout']
	GENTLE_SHUTDOWN = settings['gentle_shutdown']


def save_config(silent=False):
	"""
	Save the configuration file
	"""
	contents = {'authorized_channels': authorized_channels, 'authorized_guilds': authorized_guilds,
				'muted_channels': muted_channels, 'admin_users': admin_users, 'game': game_str,
				'skronk_timeout': skronk_timeout(), 'silent_mode': SILENT_MODE, 'save_timeout': SAVE_TIMEOUT,
				'gentle_shutdown': GENTLE_SHUTDOWN,
				}

	if not silent:
		logger.info('Writing settings to disk...')
	save_file(CONFIG_FILE_PATH, contents)


def skronk_timeout():
	return int(settings['skronk_timeout'])


def save_feature_toggle(silent=False):
	"""
	Save feature toggle map
	"""
	if not silent:
		logger.info("Writing features to disk...")
	save_file(FEATURE_FILE_PATH, enabled)


def save_votes(silent=False):
	"""
	Save vote map
	"""
	if not silent:
		logger.info('Writing votes to disk...')
	save_file(VOTE_FILE_PATH, votes)


def save_skronk(silent=False):
	"""
	Save skronk list
	"""
	if not silent:
		logger.info('Saving skronk...')
	save_file(SKRONK_FILE_PATH, skronks)


def save_all(silent=False):
	"""
	Perform all saves
	"""
	if not silent:
		logger.info('Saving to disk...')

	save_config(True)
	save_feature_toggle(True)
	save_votes(True)
	save_skronk(True)
