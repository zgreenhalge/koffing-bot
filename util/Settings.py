import os
from util import Logging
from util.File import turn_file_to_json, save_file, CONFIG_DIR_PATH

CONFIG_FILE_NAME = 'koffing.cfg'
FEATURE_FILE_NAME = "feature_toggle.cfg"
VOTE_FILE_NAME = 'vote_count.txt'
SKRONK_FILE_NAME = 'skronk.txt'
FEATURE_NAME = 'features.cfg'

CONFIG_FILE_PATH = os.path.join(CONFIG_DIR_PATH, CONFIG_FILE_NAME)
FEATURE_FILE_PATH = os.path.join(CONFIG_DIR_PATH, FEATURE_FILE_NAME)
VOTE_FILE_PATH = os.path.join(CONFIG_DIR_PATH, VOTE_FILE_NAME)
SKRONK_FILE_PATH = os.path.join(CONFIG_DIR_PATH, SKRONK_FILE_NAME)
FEATURE_PATH = os.path.join(CONFIG_DIR_PATH, FEATURE_NAME)


logger = Logging.get_logger()
cmd_prefix = '!'
settings = enabled = votes = skronks =\
		authorized_guilds = authorized_channels = muted_channels =\
		admin_users = game_str = bkg_feature_list = on_msg_feature_list =\
		SILENT_MODE = SAVE_TIMEOUT = None


def load_settings():

	global settings, enabled, votes, skronks,\
		authorized_guilds, authorized_channels, muted_channels,\
		admin_users, game_str,\
		SILENT_MODE, SAVE_TIMEOUT

	if not os.path.exists(CONFIG_DIR_PATH):
		logger.info("Creating {}...".format(CONFIG_DIR_PATH))
		os.makedirs(CONFIG_DIR_PATH)

	logger.info("Loading settings from {}...".format(CONFIG_DIR_PATH))
	settings = turn_file_to_json(CONFIG_FILE_PATH, False)
	enabled = turn_file_to_json(FEATURE_FILE_PATH, False)
	votes = turn_file_to_json(VOTE_FILE_PATH, False)
	skronks = turn_file_to_json(SKRONK_FILE_PATH, False)

	authorized_guilds = get_value_or_default(settings, 'authorized_guilds', [])
	authorized_channels = get_value_or_default(settings, 'authorized_channels', {})
	muted_channels = get_value_or_default(settings, 'muted_channels', {})
	admin_users = get_value_or_default(settings, 'admin_users', [])
	game_str = get_value_or_default(settings, 'game', '')
	SILENT_MODE = get_value_or_default(settings, 'silent_mode', False)
	SAVE_TIMEOUT = get_value_or_default(settings, 'save_timeout', 3600)

	load_features()


def load_features():
	"""
	Populate background and on-message feature class lists from file
	"""
	global bkg_feature_list, on_msg_feature_list
	features = turn_file_to_json(FEATURE_PATH, False)

	on_msg_feature_list = get_value_or_default(features, 'on_msg', [])
	bkg_feature_list = get_value_or_default(features, 'bkg', [])


def get_value_or_default(collection, key, default):
	if key in collection:
		return collection[key]

	logger.warning("Didn't find value for {}, using default {}".format(key, default))
	return default


def skronk_timeout():
	global settings
	return int(get_value_or_default(settings, 'skronk_timeout', 300))


def save_config(silent=False):
	"""
	Save the configuration file
	"""
	contents = {'authorized_channels': authorized_channels, 'authorized_guilds': authorized_guilds,
				'muted_channels': muted_channels, 'admin_users': admin_users, 'game': game_str,
				'skronk_timeout': skronk_timeout(), 'silent_mode': SILENT_MODE, 'save_timeout': SAVE_TIMEOUT,
				}
	if not silent:
		logger.info('Writing settings to disk...')
	save_file(CONFIG_FILE_PATH, contents)


def save_feature_toggle(silent=False):
	"""
	Save feature toggle map
	"""
	global enabled
	if not silent:
		logger.info("Writing features to disk...")
	save_file(FEATURE_FILE_PATH, enabled)


def save_votes(silent=False):
	"""
	Save vote map
	"""
	global votes
	if not silent:
		logger.info('Writing votes to disk...')
	save_file(VOTE_FILE_PATH, votes)


def save_skronk(silent=False):
	"""
	Save skronk list
	"""
	global skronks
	if not silent:
		logger.info('Saving skronk...')
	save_file(SKRONK_FILE_PATH, skronks)


def save_features(silent=False):
	"""
	Save feature lists
	"""
	global bkg_feature_list, on_msg_feature_list
	if not silent:
		logger.info('Saving feature lists...')
	save_file(FEATURE_PATH, {"bkg": bkg_feature_list,  "on_msg": on_msg_feature_list})


def save_all(silent=True):
	"""
	Perform all saves
	"""
	logger.info('Saving to disk...')

	save_config(silent)
	save_feature_toggle(silent)
	save_features(silent)
	save_votes(silent)
	save_skronk(silent)
