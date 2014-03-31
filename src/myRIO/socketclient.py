import socket
import sys

HOST, PORT = "localhost", 9999
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
        sock.sendall(user_in + "\n")
        
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