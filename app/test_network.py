import unittest

from FullNode import *
from TCPClient import *

class NetworkTests(unittest.TestCase):
    def setUp(self): # Called before running any test functions
        self.server_node = FullNode(consensusAlgorithm=False, existing_wallet=Wallet(""))
        self.data = {'success': True}

    def test_tcpclient_connection(self):
        client = TCPClient()
        self.assertTrue(client.connect(self.server_node.server_address), "Client could not connect")

        client.broadcast(self.data) # Sends message
        request, client_address = self.server_node.get_request() # Get received request from the server
        # Convert both to JSON objects
        server_data = json.loads(request.recv(1024).decode('utf-8'))
        client_data = json.loads(json.dumps(self.data))
        self.assertTrue(server_data == client_data, f"Client and server message not identical : client={client_data}, server={server_data}")
        # Clears the server request queue but raises an exception inside the request handler thread since the previous 'recv' already consumed the socket buffer.
        self.server_node.process_request(request, client_address)
        self.assertTrue(client.disconnect(self.server_node.server_address, clear=True))

    def tearDown(self):
        self.server_node.server_close()

if __name__ == '__main__':
    unittest.main(verbosity=2)