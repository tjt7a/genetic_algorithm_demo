import socket
import sys

ADDRESS = ("localhost", 8080)
data = " ".join(sys.argv[1:])

socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

try:
		socket.connect(ADDRESS)
		socket.sendall(data+"\n")

		received = socket.recv(1024)

finally:
		socket.close()

print "Sent: {}".format(data)
print "Received: {}".format(received)