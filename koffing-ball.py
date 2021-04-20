import sys
import os


def run_and_ret_exit_code(command):
    ret_value = os.system(command)
    if not sys.platform.startswith('win'):
        ret_value = ret_value >> 8
    return ret_value


launchCommand = "launchKoffing"
if sys.platform.startswith('win'):
    launchCommand = launchCommand + ".bat"
else:
    launchCommand = "./%s.sh" % launchCommand
ret_code = run_and_ret_exit_code(launchCommand)

'''
Run until koffing-bot returns a non-zero exit code.
Between launches of koffing-bot, attempt to pull the latest from git
'''
ret_code = run_and_ret_exit_code(launchCommand)
while ret_code == 0:
    ret_code = run_and_ret_exit_code("git pull")
    if ret_code > 0:
        print("Update failed. Git pull return code %d" % ret_code)
    ret_code = run_and_ret_exit_code(launchCommand)

print("Koffing exited with code %d" % ret_code)
