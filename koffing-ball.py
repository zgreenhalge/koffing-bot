import sys
import os

def start_koffing():
  return os.system("./launchKoffingBot.sh")

ret_code = start_koffing()
while ret_code == 0:
  ret_code = start_koffing()

print("Koffing exited with code %d" % ret_code)
