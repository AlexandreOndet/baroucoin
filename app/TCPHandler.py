import logging
import socketserver
import traceback
from typing import Callable

from app.Block import *
from app.TransactionStore import *

'''
    See https://docs.python.org/3/library/socketserver.html#request-handler-objects for reference
'''


class TCPHandler(socketserver.BaseRequestHandler):
    def handle(self):
        self.whitelistedFunctions = ['connect', 'newBlock', 'end', 'getLastBlock', 'listLastBlocks', 'getInventory', 'updateInventory']  # TODO : Load from env ?
        self.fullnode = self.server
        keep_alive = True

        while (keep_alive):
            try:
                data = b''
                recv = bytearray(4096)
                while (len(recv) >= 4096):
                    recv = self.request.recv(4096) # TODO : Add better protocol for handling multiple messages (raising JSONDecodeError at the moment)
                    data += recv

                if (data):
                    json_payload = json.loads(data.decode("utf-8"))  # TODO : Handle exceptions
                
                    self._log(logging.debug,
                              f"Received {len(data)} bytes from {self.client_address} :\n{json.dumps(json_payload, indent=4, sort_keys=True)}\n")
                    keep_alive = self.parseJSON(json_payload, self.client_address)
            except json.decoder.JSONDecodeError as e:
                self._log(logging.error, f"Could not decode JSON from raw data: data={data.decode('utf-8')}")
            except Exception as e:
                self._log(logging.error, f"Exception in TCPHandler: {traceback.format_exc()}")
                keep_alive = False

        self.request.close()
        self._log(logging.info, f"Closed connection with {self.client_address} [success]")

    def parseJSON(self, data: str, client_addr: tuple) -> bool:
        for method in list(data.keys()):
            if (method in self.whitelistedFunctions):
                return getattr(self.fullnode, 'RPC_' + method)(data[method], client_addr) # TODO: Handle deserialization exception

    def _log(self, level_func: Callable, msg: str):
        level_func(f"[{self.fullnode.id}] " + msg)
