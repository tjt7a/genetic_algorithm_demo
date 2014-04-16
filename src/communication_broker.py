'''
Code originally written by Philip Asare; modified by Tommy Tracy II initialization

'''

#import socket
import threading
import SocketServer
import pickle

'''
This script implements a basic socket server

'''

class Collision_Message:
	def __init__(self, timestamp, accel_vector):
		self.timestamp = timestamp
		self.accel_vector = accel_vector

class Start_Message:
	def __init__(self, timestamp, ip_address):
		self.timestamp = timestamp
		self.ip_address = ip_address

class Image_Message:
	def __init__(self, timestamp, image):
		self.timestamp = timestamp
		self.image = image

class Image_Message:
	
class MyRIOConnectionHandler(SocketServer.BaseRequestHandler):
    '''
    The RequestHandler class for our server.

    '''
    
    def setup(self):
        '''
        This is called the first time the myRIO connects to the server.

        '''
        cur_thread = threading.current_thread()
        print('{}:{} connected'.format(*self.client_address))
        print('Serving in {}'.format(cur_thread.name))

    def handle(self):
        '''
        This is called every time the myRIO connected to this handler sends
        a message to the server. 'self.client_address' returns a (ip, 'port')
        pair, which you can use to figure out which myRIO connected to the server
        '''
        
        # Loop so that the connection is not closed
        while True:
            # self.request is the TCP socket connected to the client
            self.data = self.request.recv(1024).strip()
            
            # check if the client closed the socket
            if len(self.data) == 0: break
            
            ### INSERT YOUR COMMUNICATION CODE HERE
            print "{} wrote:".format(self.client_address[0])
            print self.data

            message = pickle.loads(self.data)

            if type(message) is Collision_Message:
            	print("Yay! This is a collision message!")

            print(message)
            # just send back the same data, but upper-cased
            self.request.sendall(self.data.upper())
        
    def finish(self):
        print('{}:{} disconnected'.format(*self.client_address))
        
class ThreadedTCPServer(SocketServer.ThreadingMixIn, SocketServer.TCPServer):
    pass
    

if __name__ == "__main__":
    '''
    HOST := IP address of computer where broker is running (String)
    PORT := Port number that myRIOs connect to (Int > 9999)
            You may have to set your computer to allow incoming connections
            on this port number through administrative tools
    '''
    
    HOST, PORT = '', 8080 # list on port 8080 for all available interfaces

    # Create the server, binding to all interfaces on port 8080
    server = ThreadedTCPServer((HOST, PORT), MyRIOConnectionHandler)
    
    '''
    Add any variables you want to pass to the MyRIOConnectionHandler below
    as server.variable. You can initialize the variables here if necessary.
    '''
    
    # A list of connected myRIOS. This could be useful.
    server.myRIOs = {}
    
    ### INSERT OTHER VARIABLES HERE ###
    
    # Start the server thread
    server_thread = threading.Thread(target=server.serve_forever)
    
    server_thread.daemon = True
    server_thread.start()
    print "Server loop running in thread:", server_thread.name

    # Loop until Ctrl+C is pressed
    while True:
        try:
            pass
        except KeyboardInterrupt:
            server.shutdown()
            #server.server_close()
                
