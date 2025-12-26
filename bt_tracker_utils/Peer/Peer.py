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
        self.TIMEOUT = 5  # seconds
        
        self.bitfield: Optional[bytes] = None
        
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
    
    def _receive_msg(self):
        """
        Receive exactly one message from the peer.
        
        Returns:
            A dictionary representing the message received.
            the change to status will be reflected on the Peer object.
        """
        def _recv_exact(num_bytes:  int) -> bytes:
            nonlocal self
            """
            Receive exactly num_bytes from the socket.
            
            Returns:
                Bytes received, or None if connection closed
                
            Raises:
                socket.timeout: If timeout expires
            """
            data = b''
            while len(data) < num_bytes:
                chunk = self.s.recv(num_bytes - len(data)) # type: ignore
                if not chunk:
                    # Connection closed by peer
                    raise SocketClosedException(self.peer)
                data += chunk
            return data
        if not self._is_connected():
            raise SocketClosedException(self.peer)
        assert self.s is not None, "Socket is not connected" # just for type checker
        
        length_data = _recv_exact(4)
        self.s.settimeout(self.TIMEOUT) # reset timeout due to <def _read_all()>
        length = int.from_bytes(length_data, byteorder='big')
        
        if length == 0:
            return {'type': 'keep-alive'}
        
        msg_id = _recv_exact(1)
        payload = _recv_exact(length - 1)
        
        if msg_id == b'\x00':
            return {'type': 'choke'}
        elif msg_id == b'\x01':
            return {'type': 'unchoke'}
        elif msg_id == b'\x02':
            return {'type': 'interested'}
        elif msg_id == b'\x03':
            return {'type': 'not_interested'}
        elif msg_id == b'\x04' and length == 5:
            index = int.from_bytes(payload[0:4], byteorder='big')
            self._update_bitfield(have_index=index)
            return {'type': 'have', 'index': index}
        elif msg_id == b'\x05':
            bitfield = payload
            self._update_bitfield(bitfield=bitfield)
            return {'type': 'bitfield', 'bitfield': bitfield}
        # this library is not serving as a full client, msg_id 6-8 will not be implemented
        elif msg_id == b'\x06':
            return { 'type': 'request'} 
        elif msg_id == b'\x07':
            return { 'type': 'piece'}
        elif msg_id == b'\x08':
            return { 'type': 'cancel'}
        elif msg_id == b'\x09':
            return { 'type': 'port'}   # TODO: Implement DHT port messages
        elif msg_id == b'\x20':
            return { 'type': 'extend'}   # TODO: Implement extended messages
        
        raise InvalidResponseException(self.peer, f"Unknown message ID: {msg_id.hex()}")
    
    def _read_all(self):
        """Read all available data from the socket."""
        if not self._is_connected():
            raise SocketClosedException(self.peer)
        assert self.s is not None, "Socket is not connected"
        
        try:
            while True:
                self.s.settimeout(0.1) # short timeout for shorter blocks
                # long timeout will be applied in the middle of _receive_msg
                self._receive_msg()
        except socket.timeout:
            # Finish reading
            pass
        finally:
            self.s.settimeout(self.TIMEOUT)
            
    def _update_bitfield(self, bitfield: Optional[bytes] = None, have_index: Optional[int] = None):
        """Update the peer's bitfield."""
        if self.bitfield is None:
            return

        if bitfield is not None:
            self.bitfield = bitfield
        if have_index is not None:
            byte_index = have_index // 8
            bit_index = have_index % 8
            
            if byte_index < len(self.bitfield):
                self.bitfield = (self.bitfield[:byte_index] +
                                 bytes([self.bitfield[byte_index] | (1 << (7 - bit_index))]) +
                                 self.bitfield[byte_index + 1:])