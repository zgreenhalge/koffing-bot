import asyncio

from util import Feature
from util.Task import stop_running_tasks
from util.Logging import get_logger

logger = get_logger()
exit_value = 1


def ask_restart(client):
	"""
	Stop all tasks we have spawned before shutting down with return code 0.
	This signals koffing-ball.py that we should update & restart.
	"""
	serialize_background_features()
	stop_running_tasks()
	asyncio.create_task(client.close())

	logger.info('Restarting...')
	global exit_value
	exit_value = 0


def ask_exit(client):
	"""
	Stop all tasks we have spawned before shutting down with return code 1.
	This signals koffing-ball.py that we should stop the run loop.
	"""
	serialize_background_features()
	stop_running_tasks()
	asyncio.create_task(client.close())

	logger.info('Stopping...')
	global exit_value
	exit_value = 1  # return code > 0 means don't restart


def serialize_background_features():
	for feature in Feature.bkg_features:
		# Do not use TaskUtils.create_task() to avoid serializiation being short-circuited
		logger.debug("Creating task for {}.serialize()".format(type(feature).__name__))
		asyncio.create_task(feature.serialize())

		if not feature.stopping:
			feature.stopping = True
