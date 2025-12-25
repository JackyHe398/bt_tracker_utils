import socket
from typing import Optional
from ..Torrent import Torrent
from .PeerCommunicationException import *

class Peer():
    def __init__(self, peer: tuple[str, int], torrent: Torrent, self_peer_id: str):
        self.peer = peer
        self.torrent = torrent
        self.self_peer_id = self_peer_id
        self.peer_id: Optional[str] = None
        
        self.s: Optional[socket.socket] = None

        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.settimeout(5)
        self.s.connect(self.peer)
        
        
    def connect(self):
        if self.s is None or self.s.fileno() == -1:
            raise SocketClosedException(self.peer)
        msg = b'\x13BitTorrent protocol'
        msg += b'\x00' * 8  # Reserved bytes
        msg += bytes.fromhex(self.torrent.info_hash)
        msg += self.self_peer_id.encode('utf-8')
        self.s.sendall(msg)
        
        response = self.s.recv(68)
        
        # region - Validate response
        if len(response) < 68 or response[0:20] != msg[0:20]:
            raise InvalidResponseException(self.peer)
        
        if response[28:48] != bytes.fromhex(self.torrent.info_hash):
            raise InvalidResponseException(self.peer, "Info hash mismatch")
        
        self.peer_id = response[48:68].decode('utf-8', errors='ignore')
        # endregion - Validate response
        
        
    def close(self):
        if self.s:
            self.s.close()
            self.s = None
        