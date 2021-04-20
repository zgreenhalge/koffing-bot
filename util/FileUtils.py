import json
import os


def save_file(path, obj):
	"""
	Save the given data to the given file
	"""
	file = open(path, 'w')
	json_str = json.dumps(obj, sort_keys=True, indent=4)
	file.write(json_str)
	file.close()


def open_file(path, array):
	"""
	Return content of the file, or an empty array/map
	"""
	content = ''
	if not os.path.exists(path):
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
