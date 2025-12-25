import socket
from typing import Optional
from ..Torrent import Torrent
from .PeerCommunicationException import *

class Peer():
    def __init__(self, peer: tuple[str, int], torrent: Torrent, self_peer_id: str):
        self.peer = peer
        self.torrent = torrent
        self.self_peer_id = self_peer_id
        self.peer_id: Optional[bytes] = None
        
        self.s: Optional[socket.socket] = None
        
    def __enter__(self):
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_value, traceback):
        self.close()
        return False
    
    def __repr__(self):
        status = "connected" if self._is_connected else "disconnected"
        return f"Peer({self.peer[0]}:{self.peer[1]}, {status})"

    def _is_connected(self) -> bool:        
        return self.s is not None and self.s.fileno() != -1
    
    def connect(self):
        if self._is_connected():
            return
        
        try:
            # Create and connect socket
            self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.s.settimeout(5)
            self.s.connect(self.peer)
            
            # Send handshake
            msg = b'\x13BitTorrent protocol'
            msg += b'\x00' * 8  # Reserved bytes
            msg += bytes. fromhex(self.torrent.info_hash)
            msg += self.self_peer_id.encode('utf-8')
            self.s.sendall(msg)
            
            # Receive handshake response
            response = self.s.recv(68)
            
            # Validate response
            if len(response) < 68:
                raise InvalidResponseException(self.peer, "Incomplete handshake response")
            
            if response[0:20] != b'\x13BitTorrent protocol':
                raise InvalidResponseException(self.peer, "Invalid protocol")
            
            if response[28:48] != bytes. fromhex(self.torrent.info_hash):
                raise InvalidResponseException(self.peer, "Info hash mismatch")
            
            self.peer_id = response[48:68]
            
        except socket.timeout as e:
            self.close()
            raise ConnectionError(f"Connection to {self.peer} timed out")
        except socket.error as e:
            self.close()
            raise ConnectionError(f"Socket error connecting to {self.peer}:  {e}")
        except (InvalidResponseException, Exception) as e:
            self.close()
            raise
        
    def close(self):
        """Close connection to peer."""
        if self.s:
            try:
                self.s.close()
            except:
                pass
            finally:
                self.s = None
            
        