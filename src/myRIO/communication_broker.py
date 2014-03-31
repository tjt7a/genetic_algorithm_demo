#import socket
import threading
import SocketServer

'''
This script implements a basic socket server that you can extend to be your
communication broker.

'''

class MyRIOConnectionHandler(SocketServer.BaseRequestHandler):
    '''
    The RequestHandler class for our server.

    It is instantiated once per myRIO connection to the server.
    
    The functions to override (setup, handle, finish) are provided below.
    
    You will probably need other helper methods to implement your broker.
    '''
    
    def setup(self):
        '''
        This is called the first time the myRIO connects to the server.
        You may want to add more initialization functions here.
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
    
    HOST, PORT = '', 9999 # list on port 9999 for all available interfaces

    # Create the server, binding to all interfaces on port 9999
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
                
    # Activate the server; this will keep running until you
    # interrupt the program with Ctrl-C
    
    #if KeyboardInterrupt:
    #    server.shutdown()