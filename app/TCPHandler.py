import socketserver
import json

from Block import *
from TransactionStore import *

'''
    See https://docs.python.org/3/library/socketserver.html#request-handler-objects for reference
'''
class TCPHandler(socketserver.BaseRequestHandler):
    def handle(self):
        self.whitelistedFunctions = ['connect', 'newBlock', 'end'] # TODO : Load from env ?
        self.fullnode = self.server
        keep_alive = True

        while (keep_alive):
            data = self.request.recv(1024)  # TODO : Fix in case payload gets bigger than 1Kb
            text = data.decode("utf-8")
            try:
                json_payload = json.loads(text) # TODO : Handle exceptions
                print(f"[DEBUG] Received {len(data)} bytes from {self.client_address} :\n{json.dumps(json_payload, indent=4, sort_keys=True)}\n")
                keep_alive = self.parseJSON(json_payload)
            except Exception as e:
                keep_alive = False

        self.request.close()
        print(f"[+] Closed connection with {self.client_address}")

    def parseJSON(self, data: dict) -> bool:
        for method in list(data.keys()):
            if (method in self.whitelistedFunctions):
                return getattr(self, method)(data[method]) # TODO : See if general deserialization approach is feasible and handle exception on method not found

    def connect(self, data) -> bool:
        server_address = tuple(data) # TODO : Add deserialization checks
        if (self.fullnode.client.connect(server_address)):
            print(f"[*] Connected back to {server_address}...")
        else:
            print(f"[!] Already connected to {server_address} !")

        return True

    def newBlock(self, data) -> bool:
        data = json.loads(data); # TODO : Add deserialization checks
        data['transactionStore'] = TransactionStore(**data['transactionStore']);
        block = Block(**data)
        if (self.fullnode.validateNewBlock(block)):
            print(f"[+] Validated block #{block.height} (hash: {block.getHash()}) !")
            self.fullnode.blockchain.addBlock(block)
        else:
            print(f"[!] Block #{block.height} invalid: hash={block.getHash()}, lastBlock.height={self.fullnode.blockchain.lastBlock.height}")
        return True

    def end(self, data) -> bool:
        server_address = tuple(data) # TODO : Add deserialization checks
        self.fullnode.client.disconnect(server_address) # Disconnects but do not remove the peer from the peers list
        return False