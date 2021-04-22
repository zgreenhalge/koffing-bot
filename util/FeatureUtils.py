from features.AdminConsole import AdminConsole
from features.TimedSave import TimedSave

client = None
bkg_features, on_msg_features = [], []


def load_background_features():
	global client

	return [
		TimedSave(client),
	]


def load_on_message_features():
	global client

	return [
		AdminConsole(client),
	]


def get_feature_list():
	return on_msg_features + bkg_features


def spin_down_tasks(task_list):
	for task in task_list:
		if task is not None:
			task.serialize()


def load_pending_tasks(task_list):
	for task in task_list:
		if task is not None:
			task.deserialize()


def reload_tasks():
	global bkg_features, on_msg_features

	spin_down_tasks(bkg_features + on_msg_features)

	bkg_features = load_background_features()
	on_msg_features = load_on_message_features()

	load_pending_tasks(bkg_features + on_msg_features)
