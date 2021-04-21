import asyncio
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

# Create STD and ERR loggers, and their directories
# By default loggers will pipe output to an individual file in /koffing-bot/logs created at start up

print("Setting up loggers...")

logging.basicConfig(format=LOG_FORMAT, level=logging.INFO)
log_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, 'logs'))

if not os.path.exists(log_dir):
	os.makedirs(log_dir)

logHandler = logging.FileHandler(os.path.join(log_dir, 'LOG_' + date_str + '.txt'),
								 mode='a', encoding='utf-8')
logHandler.setLevel(logging.INFO)
logHandler.setFormatter(logging.Formatter(LOG_FORMAT))

logger = logging.getLogger(__name__)
logger.addHandler(logHandler)

logger.info("Stdout logger intialized")

err_logger = logging.getLogger('STDERR')
errHandler = logging.FileHandler(os.path.join(log_dir, 'ERR_' + date_str + '.txt'),
								 mode='a', encoding='utf-8')
errHandler.setFormatter(logging.Formatter(LOG_FORMAT))

err_logger.addHandler(errHandler)

sys.stderr = StreamToLogger(err_logger, logging.ERROR)


def info(message, *args):
	logger.info(message, *args)


def debug(message, *args):
	logger.debug(message, *args)


def warning(message, *args):
	logger.warning(message, *args)


def error(message, *args):
	logger.error(message, *args)
