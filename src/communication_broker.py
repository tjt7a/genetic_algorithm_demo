#!/usr/bin/env python

'''
Code originally written by Philip Asare; modified by Tommy Tracy II
This is the Communication Broker for the Genetic Algorithm System Demo
28 April 2014
'''

import threading
import SocketServer
import sys
import getopt
import Image
import random
import time
import math


# ---------- DEBUG Flags ----------

DEBUG = False # When enabled, we DEBUG with a single robot, and assume either OBSTACLE or ROBOT for every collision
ROBOT_COLLISION = True # True for Robot collision; False for Obstacle collision
SINGLE_BOT = False # Used if debugging a single robot := don't wait to start, don't send robot collision messages

DISTANCE_THRESHOLD = 100 # Threshold distance for mating robots

# -------------------- -------------- --------------------

#
# -------------------- Useful functions --------------------
#

# Display the usage
def usage():
	print('usage: communication_broker.py -i <target image filename> -f <configuration file>')

# Use an external viewer to display the image passed in as parameter
def show_image(genes):

        # Go through byte array, convert each byte into an integer (0-255) and add to list
	int_list = []
	for b in genes:
        	int_list.append(int(b))
	
        # Grab three consecutive integer values and zip them into a 3-tuple (RGB)
	tuple_list = zip(int_list[0::3],int_list[1::3],int_list[2::3])

        # Create new Image with RGB mode (size=32x16) and set the data to the tuples
	img = Image.new('RGB', (32,16))
        img.putdata(tuple_list)

        # Display the image
        img.show()

# Print contents of the data dictionary (robot states)
def print_data_dictionary():

    print("Contents of the Data Dictionary \n ----------\n")
    for color in server.myRIOs:
        string = ""
        for trait in server.myRIOs[color]:
                if trait != "genes" and trait != "second_best_genes": # We don't want to show the gene bytes
                        string += "{}:{}\t".format(trait, server.myRIOs[color][trait])
        print(string)
    print("\n ---------- \n")


# Generate a random array of bytes (random image)
def generate_random_genes():

    result = []
    for i in range(1536):
        result.append(random.randint(0,255))

    return bytearray(result)

# Print tabs to distinguish threads (index 0 thread has 0 tabs; 1 has 1 tab, etc)
def print_tabs(index):

        tabs = ""
        # Print tabs to distinguish between bots, and then the index of the thread
        for i in range(index):
                tabs += '\t'

        return tabs

# Find robots that are within the DISTANCE_THRESHOLD of this robot
def find_potential_partners(my_color):

        partners = []
        for color in server.myRIOs:
                if color != my_color and color != "webcam":
                        if close_enough(my_color, color):
                                partners.append(color)

        return partners

# Return TRUE if the two robots are considered close enough to be mating
def close_enough(color_1, color_2):
        if DEBUG:
                return True

        #print("Color_1: {} \t Color_2: {}".format(color_1, color_2))

        # Grab the current location of both robots
        color_1_location = server.myRIOs[color_1]["location"]
        color_2_location = server.myRIOs[color_2]["location"]

        #print("Robot 1 location: {} \t Robot 2 location: {}".format(color_1_location, color_2_location))

        # Split locations into x and y components on the comma
        x1 = int(color_1_location.split(",")[0])
        y1 = int(color_1_location.split(",")[1])

        x2 = int(color_2_location.split(",")[0])
        y2 = int(color_2_location.split(",")[1])

        # Calculate distance between robots
        distance = math.sqrt((x2-x1)**2 + (y2-y1)**2)

        print("\t\t\t\t\t\t\t\t\t\t Distance between {} and {}: {}".format(color_1, color_2, distance))

        # Determine if the robots are close enough
        if distance < DISTANCE_THRESHOLD:
                return True
        else:
                return False

#
# -------------------- -------------- --------------------
#


'''
The RequestHandler class for our server.

'''
class MyRIOConnectionHandler(SocketServer.BaseRequestHandler):


        '''
        This is called the first time the myRIO connects to the server.

        '''
    	def setup(self):

                # Current thread
        	cur_thread = threading.current_thread() # Start a new thread

                # Set the index of the thread
                self.thread_index = server.thread_index # Set the index of the thread
                server.thread_index += 1 # Increment the thread_index for the server

                # Display connection details
        	print('{}{}:{} connected'.format(print_tabs(self.thread_index), *self.client_address)) # Print connection details
        	print('{}Serving in {}'.format(print_tabs(self.thread_index), cur_thread.name))

                # Set state to INIT
        	self.STATE = "INIT" # State of the robot thread (always start in INIT)
            	self.COLOR = None

            	# Figure out what color myRIO is connecting
            	for color in server.myRIOs:
                	if self.client_address[0] == server.myRIOs[color]["ip"]:
                    		self.COLOR = color
				print("{}Thread's Color Set to: {}".format(print_tabs(self.thread_index), self.COLOR))
                                break

            	if self.COLOR == None and self.COLOR != "webcam":
                	print("{}**ILLEGAL ROBOT CONNECTING! UNKNOWN COLOR**".format(print_tabs(self.thread_index)))
                        exit()

                else:
                        if self.COLOR != "webcam":
                                # Set data dictionary to initial values, and print the contents
                                server.myRIOs[self.COLOR]["colliding"] = False # Is robot in collision?
                                server.myRIOs[self.COLOR]["genes"] = None # What are the robot's genes?
                                server.myRIOs[self.COLOR]["genes_ready"] = False # Are the robot's genes ready to forward?
                                server.myRIOs[self.COLOR]["second_best_genes"] = None # What is the robot's second best child's genes?
                                server.myRIOs[self.COLOR]["second_best_genes_ready"] = False # Are those ready to be forwarded?
                                server.myRIOs[self.COLOR]["second_best_genes_received"] = False # Have the 2nd best genes been received?
                                server.myRIOs[self.COLOR]["partner"] = None

                if DEBUG:
                        print_data_dictionary()

                self.PARTNER = None # Single robot is sad
        	self.STILL_RECEIVING = False # If I don't receive the complete payload; need to fill up the rest of the buffer (TCP hack)


    	def handle(self):

        	'''
        	This is called every time the myRIO connected to this handler sends
        	a message to the server. 'self.client_address' returns a (ip, 'port')
        	pair, which you can use to figure out which myRIO connected to the server
        	'''
        
        	# Loop so that the connection is not closed
        	while True:

                        # ---------- Special Conditions ----------


                        # If all data hasn't arrived yet, fill self.data with next TCP packet (TCP hack)
            		if self.STILL_RECEIVING == True:
            			self.data = self.data + self.request.recv(1538 - len(self.data))#.strip()
            		else:
            			self.data = self.request.recv(1538)#.strip()

                        # check if the client closed the socket; if so, we're done with that connection
                        if len(self.data) == 0: 
                                print("{}{} is closing connection".format(print_tabs(self.thread_index), self.COLOR))
                                break


                        # Only display data if self.data is complete
                        if not self.STILL_RECEIVING:
                                if self.COLOR != "webcam": # We don't want to see what the webcam is sending
                                        print("{}{}(Thread={}) (STATE:{}, COLOR:{}) wrote:".format(print_tabs(self.thread_index), self.client_address[0], self.thread_index, self.STATE, self.COLOR))
                                        print("{}Received({}): {}".format(print_tabs(self.thread_index), len(self.data), self.data.split(':')[0]))


                        # ---------- Special Conditions ----------

                        # ---------- If Server in DONE state ----------
            		# If server is in the DONE MODE; tell all robots and webcam to stop
            		if server.DONE == True and DEBUG == False:

            			print("{}The Server is done; return the result and stop".format(print_tabs(self.thread_index)))

            			# It's the webcam; let him know he's done
            			if self.data.startswith("W"):
            				self.response = "DONE"

            			# Robot is sending me a message
            			else:
            				self.response = "D:" + server.RESULT # Can include the final image here
            			
            			self.request.sendall(self.response) # Send the DONE message with result
            			break

                        # ---------- ---------- ---------- ----------

                        # ---------- If webcam is sending a message ----------

            		# If the webcam contacts us, update locations
            		elif self.data.startswith("W"):

            			# Do stuffs; update dictionary
                                color = (self.data.split("W:")[1]).split(":")[0]
                                location = (self.data.split("W:")[1]).split(":")[1]

                                if color in server.myRIOs:
				    server.myRIOs[color]["location"] = location # x and y are separated by commas
                                
                                if DEBUG:
                                        print("{} Webcam: Updating location:{}".format(print_tabs(self.thread_index), self.data))

            			self.request.sendall("Thanks")

                        # ---------- ---------- ---------- ----------


                        # ---------- If in any state, and we get a DONE message ----------

            		# Check if we receive a DONE message; let everyone know it's DONE time!!
            		elif self.data.startswith("D"):

                                if not DEBUG:
                                        self.STATE = "DONE" # Not strictly necessary, but to be consistent

            			if len(self.data) < 1538:
            				self.STILL_RECEIVING = True
            				continue
            			else:
            				self.STILL_RECEIVING = False

            			print("{}Received a D for Done from {} robot; setting RESULT".format(print_tabs(self.thread_index), self.COLOR))
            			
                                server.RESULT = bytearray(self.data.split("D:")[1]) # Grab the result
            			
                                if not DEBUG:
                                        server.DONE = True # Set global DONE

                                if DEBUG:
                                        print("Showing Result")
                                        show_image(server.RESULT)

            			break

                        # ---------- ---------- ---------- ----------


                        # ---------- If in the INIT state ----------

            		# If in the INIT stage ...
            		elif self.STATE == "INIT":

            			# We received an incorrect message
            			if(self.data.find("H") == -1):
            				self.response = "TRY AGAIN"
            				self.request.sendall(self.response)
            				continue

                                print("{}Received HELLO from {}".format(print_tabs(self.thread_index), self.COLOR))

                                # Wait for server.COUNT robots to connect to the Broker
                                server.COUNT -= 1

                                print("{} Server Waiting on {} robots...".format(print_tabs(self.thread_index), server.COUNT))

                                if not SINGLE_BOT:
                                        while server.COUNT > 0:
                                                pass

            			self.response = "S:"+server.target_image # Send target image

                                print("{} Sending START to {} robot".format(print_tabs(self.thread_index), self.COLOR))

            			self.request.sendall(self.response)
            			self.STATE = "DRIVE"

                        # ---------- ---------- ---------- ----------


                        # ---------- If in the DRIVE state ----------
            		elif self.STATE == "DRIVE":

            			# Robot Collided
            			if(self.data.find("C") != -1):

                                        server.myRIOs[self.COLOR]["colliding"] = True
                                        potential_partners = find_potential_partners(self.COLOR) # Return a list of potential partners (based on GVS)

            				print("{} Received a collision message from Robot {}".format(print_tabs(self.thread_index), self.COLOR))
                                        print("{} There are {} potential partners".format(print_tabs(self.thread_index), len(potential_partners)))

                                        self.PARTNER = None

                                        time.sleep(0.5) # Wait for a quarter second, and see who's available

                                        # We've been claimed!
                                        if server.myRIOs[self.COLOR]["partner"] != None:
                                                self.PARTNER = server.myRIOs[self.COLOR]["partner"]
                                                print("{}Robot {} partnered with Robot {}".format(print_tabs(self.thread_index), self.COLOR, self.PARTNER))

                                        else:
                                                for color in potential_partners:
                                                        # If someone set my partner to themselves... ive been claimed OR this dude's colliding
                                                        if server.myRIOs[color]["colliding"]:
                                                                server.lock.acquire()
                                                                server.myRIOs[color]["colliding"] = False # Set that robot to not be colliding; we have claimed it as our partner
                                                                server.myRIOs[self.COLOR]["colliding"] = False # both of us are not available anymore
                                                                server.myRIOs[color]["partner"] = self.COLOR
                                                                self.PARTNER = color
                                                                server.lock.release()
                                                                print("{}Robot {} partnered with Robot {}".format(print_tabs(self.thread_index), self.COLOR, self.PARTNER))
                                                                break # We're partnered!!!!

                                        if self.PARTNER == None:
                                                #print("{}Robot {} has no partner".format(print_tabs(self.thread_index), self.COLOR))
                                                robot_collision = False
                                                server.myRIOs[self.COLOR]["colliding"] = False
                                        else:
                                                #print("{}Robot {} has partner {}".format(print_tabs(self.thread_index), self.COLOR, self.PARTNER))
                                                robot_collision = True

                                        # Check who it collided with
            				if not robot_collision:
            					self.response = "O:" + server.target_image # O message with target image (not used)
            					print("{}Sending an Obstacle Message to {}".format(print_tabs(self.thread_index), self.COLOR))
            					self.STATE = "DRIVE"
            				else:
            					self.response = "R:" + server.target_image # R message with target image (not used)
            					print("{}Sending a Robot Message to {}".format(print_tabs(self.thread_index), self.COLOR))
                                                self.STATE = "GEN_PROT"
                                                server.myRIOs[self.COLOR]["partner"] = None

            				self.request.sendall(self.response)

                                else:
                                        print("{} ERROR: Received incorrect message from robot {}".format(print_tabs(self.thread_index), self.COLOR))

                        # ---------- ---------- ---------- ----------


                        # ---------- If in the GEN_PROT state ----------

            		elif self.STATE == "GEN_PROT":

            			if(self.data.find("G") != -1):


            				if len(self.data) < 1538:
            					self.STILL_RECEIVING = True
            					continue
            				else:
            					self.STILL_RECEIVING = False

            				print("{}{} sent a G message".format(print_tabs(self.thread_index), self.COLOR))

                                        server.myRIOs[self.COLOR]["genes"] = bytearray(self.data.split('G:')[1])
                                        server.myRIOs[self.COLOR]["genes_ready"] = True

                                        while not server.myRIOs[self.PARTNER]["genes_ready"]:
                                                pass

            				self.GENES = server.myRIOs[self.PARTNER]["genes"]

                                        print("{}Forwarding Genes from {} to {}".format(print_tabs(self.thread_index), self.COLOR, self.PARTNER))
                                        
                                        self.response = "G:" + self.GENES
                                        self.STATE = "FORWARD_GENES"

            				print("{}Showing contents of genes message".format(print_tabs(self.thread_index)))
            				show_image(self.GENES)

            				self.request.sendall(self.response)
                                        print("{}Forwarded genes".format(print_tabs(self.thread_index)))

                        # ---------- ---------- ---------- ----------


                        # ---------- If in the FORWARD_GENES state ----------
            		elif self.STATE == "FORWARD_GENES":

            			if(self.data.find("T") != -1):

            				if len(self.data) < 1538:
            					self.STILL_RECEIVING = True
                                                print("{}Didn't get the whole gene message from robot {}".format(print_tabs(self.thread_index), self.COLOR))
            					continue
            				else:
            					self.STILL_RECEIVING = False

                                        server.myRIOs[self.COLOR]["genes_ready"] = False
            				server.myRIOs[self.COLOR]["second_best_genes"] = bytearray(self.data.split('T:')[1])
                                        server.myRIOs[self.COLOR]["second_best_genes_received"] = False
                                        server.myRIOs[self.COLOR]["second_best_genes_ready"] = True

                                        print("{} Robot {} is waiting on second best genes from other".format(print_tabs(self.thread_index), self.COLOR))

                                        while not server.myRIOs[self.PARTNER]["second_best_genes_ready"]:
                                                pass

            				self.response = "T:"+server.myRIOs[self.PARTNER]["second_best_genes"]

            				self.STATE = "DRIVE"

            				print("{}Forwarding Second best child message from {} to {}".format(print_tabs(self.thread_index), self.COLOR, self.PARTNER))

            				self.request.sendall(self.response)

                                        print("{}Forwarded Second best child message from {} to {}".format(print_tabs(self.thread_index), self.COLOR, self.PARTNER))


                                        server.myRIOs[self.COLOR]["second_best_genes_received"] = True

                                        print("{}Set 2nd best genes recvd".format(print_tabs(self.thread_index)))

                                        while not server.myRIOs[self.PARTNER]["second_best_genes_received"]:
                                                pass

                                        server.myRIOs[self.COLOR]["second_best_genes_ready"] = False

                                        print("{}Set 2nd best genes ready to false".format(print_tabs(self.thread_index)))

                        # ---------- ---------- ---------- ----------


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
        opts, args  = getopt.getopt(sys.argv[1:], "hi:f:") # Arguments -c, -i, -f are required; -h is not
    except getopt.GetoptError as err:
    	usage()
        sys.exit(2)

    input_file = None
    configuration_file = None

    count = 0

    # Parse the arguments
    for opt, arg in opts:
		if opt == '-h':
			usage()
			sys.exit()
		elif opt in ("-i"):
			input_file = arg
		elif opt in ("-f"):
			configuration_file = arg

    if(input_file == None or configuration_file == None):
		usage()
		sys.exit(2)

    # Set server hostname to be local and port to 8888
    HOST, PORT = '', 8080 # list on port 8080 for all available interfaces

    # Create the server, binding to all interfaces on port 8080
    server = ThreadedTCPServer((HOST, PORT), MyRIOConnectionHandler)

    # A dictionary of connected myRIOS associating color and address
    server.myRIOs = {}
    server.thread_index = 0

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
                if color != "webcam":
		      count +=1 

    configuration.close()

    # Show robot count and contents of the data dictionary
    print("Robot Count:{}\n".format(count))

    print_data_dictionary()
    
    server.COUNT = count
    server.DONE = False
    server.img = Image.open(input_file).convert('RGB').resize((32,16))

    # convert image to byte array
    int_list = [pix for tupl in list(server.img.getdata()) for pix in tupl]
    server.target_image = bytearray(int_list)

    # This is the final image
    server.RESULT = None

    # Lock to be used by the threads to prevent a deadlock
    server.lock = threading.Lock()
    server.lock2 = threading.Lock()

    server.colliding_bots = []

    # Print target image size in bytes
    print('Target image is size: {}'.format(len(server.target_image)))
    show_image(server.target_image)

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
               
