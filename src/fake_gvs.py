import socket
import sys
import time
import Image
import io
import random

# Grid 10x10
# R---------
# ----------
# --------B-
# ----------
# ----------
# ----------
# -G--------
# ----------
# ----------
# ----------

Grid = [['-' for x in xrange(10)] for x in xrange(10)] # Create a 10x10 array of '-'s to be used as grid
locations = {}

def clear_grid():
    global Grid
    Grid = [['-' for x in xrange(10)] for x in xrange(10)] # Create a 10x10 array of '-'s to be used as grid

# Generate a random array of bytes (random image)
def generate_random_genes():

    result = []
    for i in range(1536):
        result.append(random.randint(0,255))

    return bytearray(result)

# Display the grid
def show_grid():
    global Grid
    grid = ""
    for row in Grid:
        for character in row:
            grid += character
        grid += '\n'

    grid += '\n'
    print(grid)

# Update the dictionary with locations
def update_grid():

    global locations
    global Grid

    clear_grid()
    for color in locations:
        location_x = locations[color][0]
        location_y = locations[color][1]
        Grid[location_x][location_y] = color

# Do one iteration
def iterate():

    global locations
    
    for color in locations:
        location_x = locations[color][0]
        location_y = locations[color][1]

        # Find directions that the robot can travel (0=North, 1=East, 2=South, 3=West)
        available_directions = []
        if location_x != 0:
            available_directions.append(3)
        if location_x != 9:
            available_directions.append(1)
        if location_y != 0:
            available_directions.append(0)
        if location_y != 9:
            available_directions.append(2)

        # Choose random direction
        direction = available_directions[random.randint(0,len(available_directions)-1)]

        if direction == 0:
            locations[color] = ((locations[color][0], locations[color][1]-1))
        if direction == 1:
            locations[color] = ((locations[color][0]+1, locations[color][1]))
        if direction == 2:
            locations[color] = ((locations[color][0], locations[color][1]+1))
        if direction == 3:
            locations[color] = ((locations[color][0]-1, locations[color][1]))

    update_grid()
    print locations

#HOST, PORT = "localhost", 8888

# Create a socket (SOCK_STREAM means a TCP socket)
#sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

#try:
    # Connect to server and send data
    #sock.connect((HOST, PORT))
    
'''except:
    sock.close()
    print("Could not set up socket connection")
    sys.exit(0)
'''
print('Welcome to the GVS Simulator\n')

# Initialize robots
locations["R"] = (0,0)
locations["B"] = (2,8)
locations["G"] = (6,1)

update_grid()

for i in range(100):

    show_grid()
    time.sleep(1)
    iterate()



'''
while (True):
    try:

        if user_in.find('<random>'):
            #print(generate_random_genes())
            user_in = user_in.replace('<random>', generate_random_genes())


        sock.sendall(user_in)
        
        # Receive data from the server and shut down
        received = bytearray(sock.recv(7168).split(':')[1])
        
        # display received data
        print "Sent:     {}".format(user_in)
        print "Received: {}".format(str(received))

        #img = Image.
    
        
        user_in = raw_input('> ')
    
    except:
        sock.close()
        raise
        break

sock.close()
'''
