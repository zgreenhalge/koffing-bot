import sys
import os

is_windows = sys.platform.startswith('win')


def run_and_ret_exit_code(command):
    ret_value = os.system(command)
    if not is_windows:
        ret_value = ret_value >> 8
    return ret_value


launch_cmd = "launchKoffing"
if is_windows:
    launch_cmd = "%s.bat" % launch_cmd
else:
    launch_cmd = "./%s.sh" % launch_cmd

koffing_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(koffing_dir)

ret_code = run_and_ret_exit_code(launch_cmd)
while ret_code == 0:
    print()
    print("Koffing exited with code %d" % ret_code)
    print(".")
    print("Attempting to pull the latest from git...")
    ret_code = run_and_ret_exit_code("git pull")
    if ret_code > 0:
        print("Update failed. Git pull return code %d" % ret_code)
    print(".")
    print("###############################################"*3)
    ret_code = run_and_ret_exit_code(launch_cmd)
