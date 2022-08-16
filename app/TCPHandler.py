import base64
import logging
import socketserver
import traceback
from typing import Callable

from app.Block import *
from app.TransactionStore import *

class TCPHandler(socketserver.BaseRequestHandler):
    """Handler for a new peer connection received by a node. Will keep parsing data until the connection is closed either by the peer or by the node.

    See https://docs.python.org/3/library/socketserver.html#request-handler-objects for reference.
    """
    
    def handle(self):
        # JSON Remote Procedure Calls (JSON-RPC) allowed from one peer to another. Enables the exchange of informations between peers.
        self.whitelistedFunctions = ['connect', 'newBlock', 'end', 'getLastBlock', 'listLastBlocks', 'getInventory', 'updateInventory']  # TODO : Load from env ?
        self.fullnode = self.server
        keep_alive = True

        while (keep_alive):
            try:
                data = b''
                recv = bytearray(4096)
                while (len(recv) >= 4096): # Keep reading the input buffer while there is data received
                    recv = self.request.recv(4096)
                    data += recv

                if (data): # Redundant check, should always have data at this point since 'recv' is blocking
                    data = data.decode('utf-8') # Network bytes to string 

                    # Split received JSON payloads by special character (same in TCPClient), remove the last empty string split from list
                    for raw_payload in data.split('|')[:-1]:
                        json_payload = json.loads(raw_payload)
                        decode_json_payload = json.loads(base64.b64decode(json_payload['msg']).decode('utf-8')) # Decode the payload from base64 to JSON dict
                    
                        self._log(logging.debug,
                                  f"Received {len(data)} bytes from {self.client_address} :\n{json.dumps(decode_json_payload, indent=4, sort_keys=True)}\n")
                        
                        keep_alive = self.parseJSON(decode_json_payload, self.client_address)
            except json.decoder.JSONDecodeError as e:
                self._log(logging.error, f"Could not decode JSON from raw data: raw_payload={raw_payload}, {traceback.format_exc()}")
            except Exception as e:
                self._log(logging.error, f"Exception in TCPHandler: {traceback.format_exc()}")
                keep_alive = False

        self.request.close()
        self._log(logging.info, f"Closed connection with {self.client_address} [success]")

    def parseJSON(self, data: dict, client_addr: tuple) -> bool:
        """Parses the JSON payload and calls the appropriate method on the node object."""
        for method in list(data.keys()):
            if (method in self.whitelistedFunctions):
                return getattr(self.fullnode, 'RPC_' + method)(data[method], client_addr)

    def _log(self, level_func: Callable, msg: str):
        level_func(f"H:[{self.fullnode.id}] " + msg)
