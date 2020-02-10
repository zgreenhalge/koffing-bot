import sys
import os

def run_and_ret_exit_code(command):
	ret_value = os.system(command)
	if not sys.platform.startswith('win'):
		ret_value = ret_value >> 8
	return ret_value

def start_koffing():
  return run_and_ret_exit_code("./launchKoffing.sh")

ret_code = start_koffing()
while ret_code == 0:
  ret_code = run_and_ret_exit_code("git pull")
  if ret_code > 0:
    print("Update failed. Git pull return code %d" % ret_code)
  ret_code = start_koffing()

print("Koffing exited with code %d" % ret_code)

