import SocketServer
import signal
import sys

# Handle Control-C Signal
def signal_handler(signal, frame):
	print('Killing Server...')
	server.server_close()
	sys.exit(0)


# Simple handler that will accept the first chunk of data sent by the client
class MyHandler(SocketServer.BaseRequestHandler):

	# Grab the first chunk and print out what we got and return it
	def handle(self):
			self.data = self.request.recv(1024).strip()
			print "{} wrote: ".format(self.client_address[0])
			print self.data


			self.request.sendall(self.data)


# A stream handler calls recv() several times until it encounters a newline
class MySecondHandler(SocketServer.StreamRequestHandler):

	def handle(self):
			self.data = self.rfile.readline().strip()
			print "{} wrote:".format(self.client_address[0])
			print self.data

			self.wfile.write(self.data)

if __name__ == "__main__":

	# To handle killing the server with Control-C
	signal.signal(signal.SIGINT, signal_handler)

	# Run server on port 8080
	ADDRESS = ("localhost", 8080)

	# Start server
	server = SocketServer.TCPServer(ADDRESS, MySecondHandler)
	server.serve_forever()