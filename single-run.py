import sys
import os


def run_and_ret_exit_code(command):
    ret_value = os.system(command)
    if not sys.platform.startswith('win'):
        ret_value = ret_value >> 8
    return ret_value

'''
Run koffing-bot once and print the return code
'''

launchCommand = "launchKoffing"
if sys.platform.startswith('win'):
    launchCommand = launchCommand + ".bat"
else:
    launchCommand = "./%s.sh" % launchCommand
ret_code = run_and_ret_exit_code(launchCommand)
print("Koffing exited with code %d" % ret_code)