from features.TimedSave import TimedSave


def get_background_features(client):
	return [
		TimedSave(client),
	]


def get_on_message_features(client):
	return []
