import sys
import os

is_windows = sys.platform.startswith('win')


def run_and_ret_exit_code(command):
    ret_value = os.system(command)
    if not is_windows:
        ret_value = ret_value >> 8
    return ret_value


launchCommand = "launchKoffing"
if is_windows:
    launchCommand = launchCommand + ".bat"
else:
    launchCommand = "./%s.sh" % launchCommand

ret_code = run_and_ret_exit_code(launchCommand)
while ret_code == 0:
    print("Attempting to pull the latest from git...")
    ret_code = run_and_ret_exit_code("git pull")
    if ret_code > 0:
        print("Update failed. Git pull return code %d" % ret_code)
    ret_code = run_and_ret_exit_code(launchCommand)
    print("Koffing exited with code %d" % ret_code)
