import socket
import sys

# Address of the server to connect to
ADDRESS = ("localhost", 8080)

# Data to send to the server (in this case, the command line arguments passed to the program)
data = " ".join(sys.argv[1:])

# Open a socket
socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)


# Attempt to connect to the server and send the data
try:
		socket.connect(ADDRESS)
		socket.sendall(data+"\n")

# Receive the reply
		received = socket.recv(1024)

# Finally, close the socket
finally:
		socket.close()

# Print transaction
print "Sent: {}".format(data)
print "Received: {}".format(received)