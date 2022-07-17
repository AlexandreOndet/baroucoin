import socket
import json
from typing import Tuple
import requests
import os

from utils import get_public_ip, get_all_peers

from dotenv import load_dotenv

load_dotenv()

PEERS_JSON_PATH = os.getenv("PEERS_JSON_PATH")
DNS_SERVER_IP = os.getenv("DNS_SERVER_IP")


class TCPClient(object):
    """docstring for TCPClient"""

    def __init__(self, server_addr):
        super(TCPClient, self).__init__()
        self.peers = {}  # Key : (HOST, PORT) / Value : socket representing the peer connection
        self.register_to_dns_and_fetch_peers()
        self.server_addr = server_addr

    def register_to_dns_and_fetch_peers(self):
        """
        Register this client as a full node on DNS and get all peers registered to join the network
        """
        # Starts by asking a DNS server for peers list
        peers_response = requests.get(DNS_SERVER_IP + "/new-peer")
        print(peers_response)
        myIp = get_public_ip()
        response_json = peers_response.json()
        print(response_json)
        if response_json["registeredFrom"] == myIp:
            peers = peers_response["peers"]
            with open(PEERS_JSON_PATH, 'w') as f:
                json.dump(peers, f, ensure_ascii=False, indent=4)
            for peer in peers:
                self.peers[peer] = None # Socket will be instanced later in connect method

    def send_data_to_peer(self, data, peer):
        if peer in self.peers:
            sock = self.peers[peer]
            try:
                sock.send(json.dumps(data).encode('utf-8'))
            except Exception as e:
                print("[ERROR] send: ", e)
                pass  # TODO : Handle send exception

    def answer_getLastBlock(self, peer_ip, localLastBlockHash):
        sock = self.peers[peer_ip]
        data = {
            "lastBlock": localLastBlockHash
        }
        try:
            sock.send(json.dumps(data).encode('utf-8'))
        except Exception as e:
            print("[ERROR] send: ", e)
            pass  # TODO : Handle send exception

    def connect(self, peer: Tuple[str, int]) -> bool:
        if (peer in self.peers):  # Prevent connecting back to already connected peers
            return False

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sock.connect(peer)
            self.peers[peer] = sock
            sock.send(json.dumps({'connect': self.server_addr, 'peers': self.peers}).encode(
                'utf-8'))  # Sends server listening port for the remote peer to connect
        except Exception as e:
            print("[ERROR] connect: ", e)
            return False  # TODO : Handle connect exception

        return True

    def disconnect(self, peer: Tuple[str, int], clear=False) -> bool:
        try:
            self.peers[peer].close()
        except Exception as e:
            print("[ERROR] close: ", e)
            return False  # TODO : Handle close exception

        if clear:
            del self.peers[peer]
        return True

    def broadcast(self,
                  data):  # TODO : Serialize data before or in the broadcast call ? Maybe expose a 'serialize' method from this class to FullNode ?
        for (peer, sock) in self.peers.items():
            try:
                sock.send(json.dumps(data).encode('utf-8'))
            except Exception as e:
                print("[ERROR] send: ", e)
                pass  # TODO : Handle send exception
