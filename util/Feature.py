from pydoc import locate

from features.background.BackgroundFeature import BackgroundFeature
from util import Settings
from util.Logging import get_logger
from util.Task import create_task

client = None
logger = get_logger()
bkg_features = on_msg_features = []


def load_features(feature_list):
	"""
	Do some auto-magic via pydoc to import classes at runtime
	Allowing us to avoid circular dependencies & reload tasks dynamically
	"""
	global client
	ret = []
	if feature_list is None or len(feature_list) == 0:
		return

	for class_name in feature_list:
		feature = locate(class_name)

		if feature is not None:
			logger.debug("Loaded {}".format(feature))
			ret.append(feature(client))
		else:
			logger.warning("Did not find any python object at {}".format(class_name))

	return ret


def get_feature_list():
	"""
	Returns a list of all features in use
	"""
	return on_msg_features + bkg_features


def spin_down_tasks(feature_list):
	"""
	Serializes every task, and tells background tasks to start stopping
	"""
	for feature in feature_list:
		if feature is not None:
			create_task(feature.serialize(), "{}.serialize()".format(type(feature).__name__))
			if isinstance(feature, BackgroundFeature):
				feature.stopping = True


def load_pending_tasks(feature_list):
	"""
	Deserializes every task in a given list
	"""
	for feature in feature_list:
		if feature is not None:
			create_task(feature.deserialize(), "{}.deserialize()".format(type(feature).__name__))


def reload_features():
	"""
	Spins down all tasks and serializes existing work
	Then instantiates classes from cfg and reloads the work
	"""
	global bkg_features, on_msg_features

	logger.warning("Reloading all features! Standby!")

	# Serialize everything
	spin_down_tasks(get_feature_list())

	# Reload modules listed in cfg files
	logger.info("Loading background features...")
	load_background_features()

	logger.info("Loading on_message features...")
	load_on_message_features()

	# Then deserialize pending tasks
	load_pending_tasks(get_feature_list())

	# And start background tasks again
	start_bkg_feature_tasks()


def start_bkg_feature_tasks():
	"""
	Start all our loaded background features:
		a) Make an asyncio Task out of the feature class execution
		b) Append the task to our running_tasks list
	"""
	global bkg_features

	logger.info('Starting {} background feature tasks...'.format(len(bkg_features)))
	for feature in bkg_features:
		create_task(feature.execute(), "{}.execute()".format(type(feature).__name__))


def init_features():
	if not bkg_features:
		logger.info("Loading background features...")
		load_background_features()

	if not on_msg_features:
		logger.info("Loading on_message features...")
		load_on_message_features()


def load_background_features():
	global bkg_features
	bkg_features = load_features(full_refs("background", Settings.bkg_feature_list))


def load_on_message_features():
	global on_msg_features
	on_msg_features = load_features(full_refs("onmessage", Settings.on_msg_feature_list))


def full_refs(package, feature_list):
	return ["features.{0}.{1}.{1}".format(package, name) for name in feature_list]
