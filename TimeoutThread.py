import threading
import time

class TimeoutThread (threading.Thread):

	def __init__(self, timeout, function, args):
		threading.Thread.__init__(self)
		self.timeout = timeout
		self.function = function
		self.args = args

	def run(self):
		print("Sleeping...")
		time.sleep(self.timeout)
		print("Awake!!")
		yield from self.function(*self.args)