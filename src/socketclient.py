import socket
import sys
import time
import pickle


class Collision_Message:
    def __init__(self, timestamp, accel_vector):
        self.timestamp = timestamp
        self.accel_vector = accel_vector

class Start_Message:
    def __init__(self, timestamp, ip_address):
        self.timestamp = timestamp
        self.ip_address = ip_address

HOST, PORT = "localhost", 8080
#data = " ".join(sys.argv[1:])

# Create a socket (SOCK_STREAM means a TCP socket)
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

try:
    # Connect to server and send data
    sock.connect((HOST, PORT))
    
except:
    sock.close()
    print("Could not set up socket connection")
    sys.exit(0)

print('Welcome to Client Application\nType a message to the server')
user_in = raw_input('> ')
while (user_in  != 'q'):
    try:

        msg = Start_Message(int(time.time()), user_in)

        sock.sendall(pickle.dumps(msg) + "\n")
        
        # Receive data from the server and shut down
        received = sock.recv(1024)
        
        # display received data
        print "Sent:     {}".format(user_in)
        print "Received: {}".format(received)
    
        
        user_in = raw_input('> ')
    
    except:
        sock.close()
        raise
        break

sock.close()