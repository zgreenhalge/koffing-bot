import sys
import os

def start_koffing():
  return os.system("./launchKoffingBot.sh")

ret_code = start_koffing()
while ret_code == 0:
  ret_code = os.system("git pull")
  if ret_code > 0:
    print("Update failed. Git pull return code %d" % ret_code)
  ret_code = start_koffing()

print("Koffing exited with code %d" % ret_code)

