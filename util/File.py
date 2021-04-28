import json
import os

from util.Logging import get_logger

logger = get_logger()

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir))
CONFIG_DIR_PATH = os.path.join(ROOT, 'config')


def save_file(path, obj):
	"""
	Save the given data to the given file
	"""
	with open(path, 'w') as file:
		json_str = json.dumps(obj, sort_keys=True, indent=4)
		file.write(json_str)


def open_file(path, array):
	"""
	Return content of the file, or an empty array/map
	"""
	if not os.path.exists(path):
		logger.warn("No file found at {}".format(path))
		if array:
			content = []
		else:
			content = {}
		save_file(path, content)
	elif not os.path.isfile(path):
		raise FileNotFoundError('{} does not exist as a file'.format(path))

	return open(path)


def turn_file_to_json(path, is_array):
	with (open_file(path, is_array)) as json_file:
		json_data = json.load(json_file)
		return json_data
