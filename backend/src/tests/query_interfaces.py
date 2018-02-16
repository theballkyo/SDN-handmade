
import getpass
import sys
import telnetlib 

HOST = "192.168.122.2"
# user = input("Enter your telnet username: ")
password = getpass.getpass()

tn = telnetlib.Telnet(HOST)

# tn.read_until("Username: ")
# tn.write(user + "\n")
if password:
    tn.read_until(b"Password: ")
    tn.write(password.encode("ascii") + b"\n")

tn.write(b"enable\n")
# Password for enable 
tn.write(b"cisco\n")
tn.write(b"show run | section interface\n")
mystr = ""
while True:
  r = tn.expect([b"--More--", b"#"], timeout=2)
  tn.write(b" ")
  mystr += str(r[2])
  print(mystr[-9:])
  if mystr[-9:] == "--More--'":
    mystr = mystr[:-9:]
  if r[0] == -1 and r[1] == None:
    break

tn.write(b"exit\n")
# print(mystr.split("\\r\\n"))
mystr = mystr.replace("b' \\x08\\x08\\x08\\x08\\x08\\x08\\x08\\x08\\x08        \\x08\\x08\\x08\\x08\\x08\\x08\\x08\\x08\\x08 ", "\n")
mystr = mystr.replace("'b'", "")
print("\n".join(mystr.split("\\r\\n")))
