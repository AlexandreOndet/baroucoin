import base64
import json
import logging
import os
import requests
import socket
from dotenv import load_dotenv
from typing import Tuple

load_dotenv()

PEERS_JSON_PATH = os.getenv("PEERS_JSON_PATH")
DNS_SERVER_IP = os.getenv("DNS_SERVER_IP")


class TCPClient(object):
    """docstring for TCPClient"""

    def __init__(self, server_addr):
        super(TCPClient, self).__init__()
        # TODO: simplifiy peer structure using only sockets attributes (see https://docs.python.org/3/library/socket.html?highlight=socket#socket.socket.getpeername)
        self.peers = {}  # Key : (HOST, PORT) / Value : socket representing the peer connection
        self.server_addr = server_addr
        # self.register_to_dns_and_fetch_peers()
        # self.connect_to_all_peers()

    def __del__(self):
        for peer in self.peers:
            self.disconnect(peer)

    def connect_to_all_peers(self):
        for peer in self.peers.keys():
            self.connect(peer)

    def register_to_dns_and_fetch_peers(self):
        """
        Register this client as a full node on DNS and get all peers registered to join the network
        """
        # Starts by asking a DNS server for peers list
        peers_response = requests.get(DNS_SERVER_IP + "/new-peer")
        print(peers_response)
        myIp = requests.get('https://api.ipify.org').text  # Fetch own public IP
        response_json = peers_response.json()
        print(response_json)
        if response_json["registeredFrom"] == myIp:
            peers = peers_response["peers"]
            with open(PEERS_JSON_PATH, 'w') as f:
                json.dump(peers, f, ensure_ascii=False, indent=4)
            for peer in peers:
                host, port = tuple(peer.split(':'))
                self.peers[(host, int(port))] = None  # Socket will be instanced later in connect method

    def send_data_to_peer(self, data: dict, peer: Tuple[str, int]):
        logging.debug(f"Trying to send {data} to {peer}")
        if peer in self.peers:
            sock = self.peers[peer]
            try:
                sock.send(self._encapsulateMsg(json.dumps(data)))
            except Exception as e:
                logging.error(f" In send_data_to_peer : {e}")
        else:
            logging.error(f" TCPClient : Could not find {peer} in {self.peers} ")

    def connect(self, peer: Tuple[str, int]) -> bool:
        if peer in self.peers:  # Prevent connecting back to already connected peers
            return False

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sock.connect(peer)
            self.peers[peer] = sock
            data = {'connect': {'server_address': self.server_addr, 'peers': list(self.peers.keys())}}
            sock.send(self._encapsulateMsg(json.dumps(data)))  # Sends server listening port for the remote peer to connect
        except Exception as e:
            logging.error(f"connect: {e}")
            return False  # TODO : Handle connect exception

        return True

    def disconnect(self, peer: Tuple[str, int], clear=False) -> bool:
        if not peer in self.peers:
            return False

        try:
            self.peers[peer].close()
        except Exception as e:
            logging.error(f"close: {e}")
            return False  # TODO : Handle close exception

        if clear:
            del self.peers[peer]
            
        return True

    def broadcast(self, data: dict):
        for (peer, sock) in list(self.peers.items()):
            try:
                sock.send(self._encapsulateMsg(json.dumps(data)))
            except BrokenPipeError as e:
                logging.error(f"broadcasting: {e} to {peer}")
            except Exception as e:
                logging.error(f"Unexpected error during broadcasting: {e}")

    '''
        Encaspulate the 'msg' data by converting it to base64 and wrapping it in a JSON object with special character delimiter '|' for separating messages
        TODO: Could add a checksum and replace the use of special character with a data length prefix
    '''
    def _encapsulateMsg(self, msg: str) -> bytes:
        return (json.dumps({'msg': base64.b64encode(msg.encode('utf-8')).decode('utf-8')}) + '|').encode('utf-8')
