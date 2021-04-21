import logging
import os
import sys

from util import DateTimeUtils


class StreamToLogger(object):
	"""
	Fake stream-like object that redirects writes to a logger instance.
	"""

	def __init__(self, wrapped, log_level):
		self.logger = wrapped
		self.log_level = log_level
		self.linebuf = ''

	def write(self, buf):
		if not buf.isspace():
			for line in buf.splitlines():
				if line:
					self.logger.log(self.log_level, line)

	def flush(self):
            return
        # do nothing (:


LOG_FORMAT = '[%(asctime)-15s] [%(levelname)+7s] [%(threadName)+10s] [%(thread)d] [%(module)s.%(funcName)s] - %(message)s'
date_str = DateTimeUtils.get_current_date_string()

# Create log handlers for writing to file, STD and ERR
# By default loggers will pipe output to an individual file in /koffing-bot/logs created at start up
# If the directories don't exist, we just make em

print("Setting up loggers...")

log_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, 'logs'))

if not os.path.exists(log_dir):
	os.makedirs(log_dir)

formatter = logging.Formatter(LOG_FORMAT)

stdHandler = logging.StreamHandler(sys.stdout)
stdHandler.setLevel(logging.INFO)
stdHandler.setFormatter(formatter)

fileHandler = logging.FileHandler(os.path.join(log_dir, 'LOG_' + date_str + '.txt'), mode='a', encoding='utf-8')
fileHandler.setLevel(logging.INFO)
fileHandler.setFormatter(formatter)

errHandler = logging.FileHandler(os.path.join(log_dir, 'ERR_' + date_str + '.txt'), mode='a', encoding='utf-8')
errHandler.setFormatter(logging.Formatter(LOG_FORMAT))
errHandler.setLevel(logging.WARNING)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(fileHandler)
logger.addHandler(stdHandler)
logger.addHandler(errHandler)

# Enable below to force print() statements through our logger
# sys.stdout = StreamToLogger(logger, logging.INFO)

logger.info("Stdout logger intialized")


def get_logger():
	return logger
