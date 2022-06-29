import socket
import json
from typing import Tuple

class TCPClient(object):
    """docstring for TCPClient"""
    def __init__(self, server_addr):
        super(TCPClient, self).__init__()
        self.peers = {} # Key : (HOST, PORT) / Value : socket reprensenting the peer connection
        self.server_addr = server_addr

    def connect(self, peer: Tuple[str, int]) -> bool:
        if (peer in self.peers): # Prevent connecting back to already connected peers
            return False

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sock.connect(peer)
            self.peers[peer] = sock
            sock.send(json.dumps({'connect': self.server_addr}).encode('utf-8')) # Sends server listening port for the remote peer to connect
        except Exception as e:
            print("[ERROR] connect: ", e)
            return False # TODO : Handle connect exception

        return True

    def disconnect(self, peer: Tuple[str, int], clear=False) -> bool:
        try:
            self.peers[peer].close()
        except Exception as e:
            print("[ERROR] close: ", e)
            return False # TODO : Handle close exception

        if clear:
            del self.peers[peer]
        return True

    def broadcast(self, data): # TODO : Serialize data before or in the broadcast call ? Maybe expose a 'serialize' method from this class to FullNode ?
        for (peer, sock) in self.peers.items():
            try:
                sock.send(json.dumps(data).encode('utf-8'))
            except Exception as e:
                print("[ERROR] send: ", e)
                pass # TODO : Handle send exception