import asyncio
import sys

from util import Settings
from util.LoggingUtils import get_logger

logger = get_logger()
task_list = []


def stop_tasks(client):
	"""
	Stop all tasks in the task list that we've accumulated so far
	Then wait for the client to logout
	"""
	logger.info('Stopping tasks...')
	global task_list

	for task in task_list:
		task.cancel()

	end_client_session(client)


def ask_restart(client):
	"""
	Stop all tasks we have spawned before shutting down with return code 0.
	This signals koffing-ball.py that we should update & restart.
	"""
	stop_tasks(client)
	logger.info('Restarting...')
	sys.exit(0)


def ask_exit(client):
	"""
	Stop all tasks we have spawned before shutting down with return code 1.
	This signals koffing-ball.py that we should stop the run loop.
	"""
	stop_tasks(client)
	logger.info('Stopping...')
	sys.exit(1)  # return code > 0 means don't restart


def end_client_session(client):
	"""
	Shutdown the client and bring koffing offline. Goodbye old friend.
	"""
	gentle_shutdown = Settings.GENTLE_SHUTDOWN

	# Loop until all our background tasks have completed
	# Good in theory, PITA in practice
	# The reference to FeatureUtils results in a circular dependency via AdminConsole...

	# if gentle_shutdown:
	# 	self.logger.warning('Gentle shutdown enabled for {} tasks'.format(len(FeatureUtils.bkg_features)))
	# 	done_stopping = False
	# 	loop_count = 1
	# 	start_time = DateTimeUtils.now()
	#
	# 	while not done_stopping:
	# 		done_stopping = True
	# 		for task in FeatureUtils.bkg_features:
	# 			if not task.stopping:
	# 				task.stopping = True
	# 			if not task.stopped:
	# 				done_stopping = False
	#
	# 		if loop_count % 500000000 == 0:
	# 			now = DateTimeUtils.now()
	# 			self.logger.info("Not done stopping after {}".format(str(now - start_time)[0:10]))
	# 		loop_count += 1

	# Finally, logout
	logger.info('Stopping main client...')
	asyncio.ensure_future(client.close())
