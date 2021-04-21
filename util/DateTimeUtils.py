import pytz

from datetime import datetime

date_format = '%Y-%m-%d'
pretty_date_format = '%a %b %d %Y %I:%M:%S %p'
est_tz = pytz.timezone('US/Eastern')

def date_to_string(date):
	"""
	Turn a date object into a string formatted the way we want (YYYY-mm-dd)
	"""
	return date.strftime(pretty_date_format)


def string_to_date(string):
	"""
	Turn a string in YYYY-mm-dd into a date object
	"""
	return datetime.strptime(string, pretty_date_format).date()


def get_date():
	"""
	Returns a string of the current date in mm-dd-YYYY
	"""
	global est_tz
	return datetime.now(tz=est_tz).strftime('%m-%d-%Y')