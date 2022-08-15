import unittest
import warnings

from app.FullNode import *
from app.TCPClient import *

class NetworkTests(unittest.TestCase):
    def _decode_payload(self, raw_data: bytes) -> dict:
        json_payload = json.loads(raw_data.decode('utf-8').split('|')[0])
        return json.loads(base64.b64decode(json_payload['msg']).decode('utf-8'))

    @classmethod
    def setUpClass(self): # Called before running any test functions
        warnings.filterwarnings(action="ignore", message="unclosed", category=ResourceWarning) # Clear the unclosed sockets warning for tests
        self.server_node = FullNode(consensusAlgorithm=False, existing_wallet=Wallet(""))

    def test_tcpclient_connection(self):
        client = TCPClient(server_addr=self.server_node.server_address)
        self.assertTrue(client.connect(self.server_node.server_address), f"Client could not connect : server_address={self.server_node.server_address}")

        request, client_address = self.server_node.get_request() # Get received 'connect' request from the server
        
        # Extract payload from base64 message
        server_data = self._decode_payload(request.recv(4096))
        client_data = json.loads(json.dumps({'connect': {'server_address': self.server_node.server_address, 'peers': [self.server_node.server_address]}}))

        self.assertTrue(server_data == client_data, f"Client and server message not identical : client={client_data}, server={server_data}")
        self.assertTrue(client.disconnect(self.server_node.server_address, clear=True))

    def test_peers_connection(self):
        peer = FullNode(consensusAlgorithm=False, existing_wallet=Wallet("peer"), server_address=('127.0.0.1', 12345)) # Create new peer

        self.assertTrue(self.server_node.client.connect(peer.server_address), f"Server could not connect to peer : peer={peer.server_address}") # Send a 'connect' request to peer in the process
        self.assertIn(peer.server_address, self.server_node.client.peers, f"Peer not added to the server's client list : peer={peer.server_address}, peers={self.server_node.client.peers}")

        request, _ = peer.get_request()
        connect_payload = self._decode_payload(request.recv(4096))
        server_address_payload = tuple(connect_payload['connect']['server_address'])

        self.assertGreater(len(connect_payload), 0, f"Peer did not receive the JSON 'connect' request : request={request}")
        self.assertIn('connect', connect_payload, f"Malformed JSON 'connect' payload : payload={connect_payload}")
        self.assertEqual(server_address_payload, 
                    self.server_node.server_address, 
                    f"JSON 'connect' address does not match server address : payload={server_address_payload}, server_address={self.server_node.server_address}")
        self.assertTrue(peer.client.connect(server_address_payload), f"Peer could not connect back to server : payload={server_address_payload}")
        self.assertIn(self.server_node.server_address, peer.client.peers, f"Server not added to the peer's client list : server_address={self.server_node.server_address}, peers={peer.client.peers}")

        request, _ = self.server_node.get_request()
        connect_payload = self._decode_payload(request.recv(4096))
        server_address_payload = tuple(connect_payload['connect']['server_address'])

        self.assertFalse(self.server_node.client.connect(server_address_payload), 
                    f"Server tried to connect back to peer but is already connected : peer={server_address_payload}, peers={self.server_node.client.peers}")
        self.assertTrue(peer.client.disconnect(self.server_node.server_address, clear=True))

if __name__ == '__main__':
    unittest.main(verbosity=2)