from typing import Optional

class PeerCommunicationException(Exception):
    """Exception raised for errors in peer communication."""
    default_message = "Peer communication error"
    
    def __init__(self, peer: Optional[tuple[str, int]] = None, message=None):
        message = message or self.default_message
        if peer:
            message += f" with peer '{peer[0]}:{peer[1]}'"
        super().__init__(message or self.default_message)
        
class SocketClosedException(PeerCommunicationException):
    """Exception raised when the socket is closed unexpectedly."""
    default_message = "Socket closed unexpectedly"
    def __init__(self, peer: Optional[tuple[str, int]] = None, message=None):
        super().__init__(peer, self.default_message)
        message = message or self.default_message
        if peer:
            message += f" with peer '{peer[0]}:{peer[1]}'"
        super().__init__(message=message)
    
class InvalidResponseException(PeerCommunicationException):
    """Exception raised for invalid responses from peers."""
    default_message = "Invalid response received"
    
    def __init__(self, peer: Optional[tuple[str, int]] = None, message=None):
        message = message or self.default_message
        if peer:
            message += f" from peer '{peer[0]}:{peer[1]}'"
        super().__init__(message=message)