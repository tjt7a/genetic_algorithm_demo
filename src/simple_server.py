import SocketServer

# Simple handler that will accept the first chunk of data sent by the client
class MyHandler(SocketServer.BaseRequestHandler):

	def handle(self):
			self.data = self.request.recv(1024).strip()
			print "{} wrote: ".format(self.client_address[0])
			print self.data

			self.request.sendall(self.data.upper())

# A stream handler calls recv() several times until it encounters a newline
class MySecondHandler(SocketServer.StreamRequestHandler):

	def handle(self):
			self.data = self.rfile.readline().strip()
			print "{} wrote:".format(self.client_address[0])
			print self.data
			self.wfile.write(self.data.upper())

if __name__ == "__main__":
	ADDRESS = ("localhost", 8080)

	server = SocketServer.TCPServer(ADDRESS, MySecondHandler)
	server.serve_forever()