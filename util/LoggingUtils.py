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


# Filters for messages below WARNING level
class InfoFilter(logging.Filter):
    def filter(self, rec):
        return logging.NOTSET <= rec.levelno < logging.WARNING


# Filters for messages between WARNING and CRITICAL level
class WarningFilter(logging.Filter):
    def filter(self, rec):
        return logging.WARNING <= rec.levelno <= logging.CRITICAL


LOG_FORMAT = '[%(asctime)-15s] [%(levelname)+7s] [%(threadName)+10s] [%(thread)d] [%(module)s.%(funcName)s] - %(message)s'
date_str = DateTimeUtils.get_current_date_string()
formatter = logging.Formatter(LOG_FORMAT)


def init_std_handler(handler):
	handler.setLevel(logging.DEBUG)
	handler.addFilter(InfoFilter())
	handler.setFormatter(formatter)
	return handler


def init_err_handler(handler):
	handler.setLevel(logging.WARNING)
	handler.addFilter(WarningFilter())
	handler.setFormatter(formatter)
	return handler


# Create log handlers for writing to file, STD and ERR
# By default we pipe output to two files in /koffing-bot/logs created at start up
# There is only ever 1 static logger tho

print("Setting up loggers...")

log_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, 'logs'))

if not os.path.exists(log_dir):
	os.makedirs(log_dir)

std_stream_handler = logging.StreamHandler(sys.stdout)
init_std_handler(std_stream_handler)

std_file_handler = logging.FileHandler(os.path.join(log_dir, 'LOG_' + date_str + '.txt'), mode='a', encoding='utf-8')
init_std_handler(std_file_handler)

err_stream_handler = logging.StreamHandler(sys.stderr)
init_err_handler(err_stream_handler)

err_file_handler = logging.FileHandler(os.path.join(log_dir, 'ERR_' + date_str + '.txt'), mode='a', encoding='utf-8')
init_err_handler(err_file_handler)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(std_stream_handler)
logger.addHandler(std_file_handler)
logger.addHandler(err_stream_handler)
logger.addHandler(err_file_handler)

# Enable below to force print() statements through our logger
# sys.stdout = StreamToLogger(logger, logging.INFO)

logger.info("Stdout logger intialized")


def get_logger():
	return logger
