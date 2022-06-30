import socketserver
import json

from Block import *
from TransactionStore import *

'''
    See https://docs.python.org/3/library/socketserver.html#request-handler-objects for reference
'''
class TCPHandler(socketserver.BaseRequestHandler):
    def handle(self):
        self.fullnode = self.server
        keep_alive = True

        while (keep_alive):
            data = self.request.recv(1024)  # TODO : Fix in case payload gets bigger than 1Kb
            text = data.decode("utf-8")
            json_payload = json.loads(text) # TODO : Handle exceptions
            print(f"[DEBUG] Received {len(data)} bytes from {self.client_address} :\n{json.dumps(json_payload, indent=4, sort_keys=True)}\n")

            keep_alive = self.parseJSON(json_payload)

        self.fullnode.client.disconnect(self.client_address) # Disconnects but do not remove the peer from the peers list
        self.request.close()
        print(f"[+] Closed connection with {self.client_address}")

    def parseJSON(self, data: dict) -> bool:
        # TODO : Create dict of functions to match the JSON attributes sent in the message
        if ("connect" in data):
            server_address = tuple(data['connect'])
            if (self.fullnode.client.connect(server_address)):
                print(f"[*] Connected back to {server_address}...")
            else:
                print(f"[!] Already connected to {server_address} !")
        elif ("newBlock" in data):
            b = json.loads(data["newBlock"], object_hook=lambda d: Block(**d) if ("miner" in d) else TransactionStore(**d)) # TODO : Write proper JSON decoder for objects
            print(b)
            if (self.fullnode.validateNewBlock(b)):
                print(f"[+] Validated block #{b.height} (hash: {b.getHash()}) !")
                self.fullnode.blockchain.addBlock(b)
            else:
                print(f"[!] Block #{b.height} invalid: hash={b.getHash()}, lastBlock.height={self.fullnode.blockchain.lastBlock.height}")
        elif ("end" in data):
            return False

        return True