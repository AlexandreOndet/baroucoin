import socket
import json
from typing import Tuple

class TCPClient(object):
    """docstring for TCPClient"""
    def __init__(self):
        super(TCPClient, self).__init__()
        self.peers = {} # Key : (HOST, PORT) / Value : socket reprensenting the peer connection

    def connect(self, peer: Tuple[str, int]) -> bool:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sock.connect(peer)
            self.peers[peer] = sock
        except Exception as e:
            print("Error connect: ", e)
            return False # TODO : Handle connect exception

        return True

    def disconnect(self, peer: Tuple[str, int], clear=False) -> bool:
        try:
            self.peers[peer].close()
        except Exception as e:
            print("Error disconnect: ", e)
            return False # TODO : Handle close exception

        if clear:
            del self.peers[peer]
        return True

    def broadcast(self, data): # TODO : Serialize data before or in the broadcast call ? Maybe expose a 'serialize' method from this class to FullNode ?
        for (peer, sock) in self.peers.items():
            try:
                sock.send(json.dumps(data).encode('utf-8'))
            except Exception as e:
                print("Error send: ", e)
                pass # TODO : Handle send exception

if __name__ == "__main__":
    HOST, PORT = "localhost", 13337
    data = {
    "name": "hello, I am Tom.",
    "age": 10,
    "info": "sample is simple."
    }

    client = TCPClient()
    client.connect((HOST, PORT))
    client.broadcast(data)
    client.disconnect((HOST, PORT))