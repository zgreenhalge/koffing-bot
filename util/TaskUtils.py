import asyncio

from util.LoggingUtils import get_logger

running_tasks = []
logger = get_logger()
shutdown_timeout = 60


def create_task(coroutine, name=None):
	"""
	Helper function to create an asyncio Task from outside a coroutine
	And add it to our running_Tasks list
	"""
	if name is None or name == "":
		name = coroutine.__qualname__  # Default name to make sure logs are at least somewhat descriptive

	logger.debug("Creating task for {}".format(name))
	task = asyncio.create_task(coroutine)
	task.set_name(name)
	running_tasks.append(task)
	return task


def stop_running_tasks():
	"""
	Stop all the tasks that we've kept track of
	NOTE - this will *not* stop all tasks on the event loop!
	"""
	global running_tasks
	logger.debug('Stopping {} running tasks...'.format(len(running_tasks)))
	stop_tasks(running_tasks)


def stop_task(task):
	if task.done():
		logger.debug("{} completed successfully.".format(task.get_name()))
		ret = 1
	else:
		logger.debug("{} not complete, cancelling.".format(task.get_name()))
		task.cancel()  # Causes CancelledError during next iteration of event loop
		ret = 0

	if task in running_tasks:
		running_tasks.remove(task)

	return ret


def stop_tasks(task_list):
	"""
	Cancel any incomplete tasks in the list
	"""
	num_completed = 0

	for task in task_list:
		num_completed += stop_task(task)

	logger.info("{} tasks completed, {} cancelled.".format(num_completed, len(task_list) - num_completed))
