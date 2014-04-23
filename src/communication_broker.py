#!/usr/bin/env python

'''
Code originally written by Philip Asare; modified by Tommy Tracy II
This is the Communication Broker for the Genetic Algorithm System

'''

#import socket
import threading
import SocketServer
import sys
import getopt
import Image
import random


def usage():
	print('usage: communication_broker.py -c <count> -i <target image filename> -f <configuration file>')

def show_image(genes):
	int_list = []
	for b in genes:
        	int_list.append(int(b))
	
	tuple_list = zip(int_list[0::3],int_list[1::3],int_list[2::3])

	img = Image.new('RGB', (32,16))
        img.putdata(tuple_list)
        img.show()

def generate_random_genes():

    result = []
    for i in range(1536):
        result.append(random.randint(0,255))

    return bytearray(result)



class MyRIOConnectionHandler(SocketServer.BaseRequestHandler):


	'''
    The RequestHandler class for our server.

   	'''
    
    	def setup(self):

        	'''
        	This is called the first time the myRIO connects to the server.

        	'''
        	cur_thread = threading.current_thread() # Start a new thread

        	print('{}:{} connected'.format(*self.client_address)) # Print connection details
        	print('Serving in {}'.format(cur_thread.name))

        	self.STATE = "INIT" # State of the robot thread (always start in INIT)
        	self.COLOR = None # Color of the robot
        	self.GENES = None # Genes of the robot
        	self.PARTNER = None # Color of the partner
        	self.PARTNER_GENES = None
        	self.STILL_RECEIVING = False # If I don't receive the complete payload; need to fill up the rest of the buffer


    	def handle(self):
        	'''
        	This is called every time the myRIO connected to this handler sends
        	a message to the server. 'self.client_address' returns a (ip, 'port')
        	pair, which you can use to figure out which myRIO connected to the server
        	'''
        
        	# Loop so that the connection is not closed
        	while True:

            		# self.request is the TCP socket connected to the client
            		if self.STILL_RECEIVING == True:
            			self.data = self.data + self.request.recv(1538 - len(self.data)).strip()
            		else:
            			self.data = self.request.recv(1538).strip()
            
            		# check if the client closed the socket; if so, we're done
            		if len(self.data) == 0: 
            			break
            
            		# dump contents
            		print("{} (STATE:{}, COLOR:{}) wrote:".format(self.client_address[0], self.STATE, self.COLOR))
            		#print("Received: ", self.data)
            		print("Size:  ", len(self.data))

            		# If server is in the DONE MODE; tell all robots and webcam to stop
            		if server.DONE == True:

            			print("We're done")
            			# It's the webcam; let him know he's done
            			if self.data.startswith("W"):
            				self.response = "DONE"

            			# Robot is sending me a message
            			else:
            				self.response = "D:" + server.RESULT #Can include the final image here
            			
            			show_image(server.RESULT)

            			self.request.sendall(self.response)

            			break

            		# If the webcam contacts us, update locations
            		elif self.data.startswith("W"):
            			# Do stuffs; update dictionary
            			print("Webcam")
            			print(self.data)

            			self.request.sendall("Thanks")

            		# Check if we receive a DONE message; let everyone know it's DONE time!!
            		elif self.data.startswith("D"):

            			if len(self.data) < 1538:
            				self.STILL_RECEIVING = True
            				continue
            			else:
            				self.STILL_RECEIVING = False

            			print("Received a D for Done")
            			print("Received this many bytes: ", len(self.data))
            			server.RESULT = bytearray(self.data.split("D:")[1]) # Grab the result
            			server.DONE = True # Set global DONE

            			int_list = []

            			print("Showing Result")
            			show_image(server.RESULT)

            			break

            		# If in the INIT stage ...
            		elif self.STATE == "INIT":

            			print("We're in the init state")

            			# We received an incorrect message
            			if(self.data.find("H") == -1):
            				self.response = "TRY AGAIN"
            				self.request.sendall(self.response)
            				continue

            			self.response = "S:"+server.target_image # Send target image
            			self.request.sendall(self.response)
            			self.STATE = "DRIVE"

            			print("RECEIVE a HELLO MESSAGE")
            			print("Sending a START message")

            		elif self.STATE == "DRIVE":

            			# Robot Collided
            			if(self.data.find("C") != -1):

            				print("Received a collision message")
            				# Check who it collided with

            				if random.random() < 0.5:
            					self.response = "O:" + server.target_image
            					print("Sending an obstacle message")
            					self.STATE = "DRIVE"
            					print("Sending an O: message")
            				else:
            					self.response = "R:" + server.target_image
            					self.PARTNER = None #Set to a partner
            					self.STATE = "GEN_PROT"
            					print("Sending an R: message")

            				self.request.sendall(self.response)


            		elif self.STATE == "GEN_PROT":

            			if(self.data.find("G") != -1):


            				if len(self.data) < 1538:
            					self.STILL_RECEIVING = True
            					continue
            				else:
            					self.STILL_RECEIVING = False

            				print("In GEN_PROT state")
            				print("Got a G message of size: ", len(self.data))


            				self.GENES = bytearray(self.data.split('G:')[1])

            				self.response = "G:" + generate_random_genes()
            				self.STATE = "FORWARD_GENES"

            				print("Showing contents of genes message")
            				show_image(self.GENES)

            				print("Sending G: message with random image")

            				print("Showing contents of sent G message")
            				show_image(self.response)

            				self.request.sendall(self.response)

            		elif self.STATE == "FORWARD_GENES":


            			if(self.data.find("T") != -1):


            				if len(self.data) < 1538:
            					self.STILL_RECEIVING = True
            					continue
            				else:
            					self.STILL_RECEIVING = False

            				print("In Forward_Genes state")
            				print("Received Forward Genes")

            				self.PARTNER_GENES = bytearray(self.data.split('T:')[1])

            				self.response = "T:"+generate_random_genes()
            				self.STATE = "DRIVE"

            				print("Showing contents of T message")

            				show_image(self.PARTNER_GENES)

            				print("Sending random image as T response")
            				print("Showing contents of sent T message")
            				show_image(self.response)

            				self.request.sendall(self.response)




	def finish(self):
        	print('{}:{} disconnected'.format(*self.client_address))
        
class ThreadedTCPServer(SocketServer.ThreadingMixIn, SocketServer.TCPServer):
	pass
    

	'''
    	HOST := IP address of computer where broker is running (String)
    	PORT := Port number that myRIOs connect to (Int > 9999)
            You may have to set your computer to allow incoming connections
            on this port number through administrative tools
    	'''

if __name__ == "__main__":


    try:
        opts, args  = getopt.getopt(sys.argv[1:], "hc:i:f:") # Arguments -c, -i, -f are required; -h is not
    except getopt.GetoptError as err:
    	usage()
        sys.exit(2)

    input_file = None
    configuration_file = None

    count = 0

    for opt, arg in opts:
		if opt == '-h':
			usage()
			sys.exit()
		elif opt in ("-i"):
			input_file = arg
		elif opt in ("-f"):
			configuration_file = arg
		elif opt in ("-c"):
			count = arg

    if(input_file == None or count == 0 or configuration_file == None):
		usage()
		sys.exit(2)


    HOST, PORT = '', 8888 # list on port 8080 for all available interfaces

	# Create the server, binding to all interfaces on port 8080
    server = ThreadedTCPServer((HOST, PORT), MyRIOConnectionHandler)


	# A dictionary of connected myRIOS associating color and address
    server.myRIOs = {}

	# Open the configuration file
    try:
		configuration = open(configuration_file, 'r')
    except:
		print("Cannot read configuration file")
		exit(2)

	# Parse configuration file
    for config in configuration:
		color = config.split(':')[0]
		ip = config.split(':')[1].strip()
		server.myRIOs[color] = {}
		server.myRIOs[color]["ip"] = ip

    print(server.myRIOs)

    
    server.DONE = False
    server.partnersGenes = {}

    server.img = Image.open(input_file).convert('RGB').resize((32,16))
    server.img.show()

	#[element for tupl in tupleOfTuples for element in tupl]
    int_list = [pix for tupl in list(server.img.getdata()) for pix in tupl]
    server.target_image = bytearray(int_list)

	# This is the final image
    server.RESULT = None

	# Print target image size in bytes
    print("Target image is size: ",len(server.target_image))
    
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
                
