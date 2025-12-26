from typing import Optional
from enum import Enum

class TorrentStatus(Enum):
    COMPLETED = 1
    STARTED = 2
    STOPPED = 3

class Torrent:
    """Represents a torrent instance, encapsulating tracker and metadata information."""
    def __init__(self, info_hash: str,
            total_size: int, left: Optional[int] = None,
            downloaded: int = 0, uploaded: int = 0,
            event: TorrentStatus = TorrentStatus.STARTED):
        """
        Initialize a Torrent object.

        Args:
            info_hash (str): The unique identifier of the torrent.
            total_size (int): The total size of the torrent in bytes.
            left (int): The number of bytes still needed to complete. Defaults to (total_size - downloaded).
            downloaded (int): The number of bytes downloaded. Defaults to 0.
            uploaded (int): The number of bytes uploaded. Defaults to 0.
            num_want (int|None): The number of peers requested. Defaults to None.
            event (TorrentStatus): The current tracker event. Defaults to TorrentStatus.STARTED.

        Raises:
            ValueError: If total_size is not a positive integer.
        """
        
        # data validation
        assert isinstance(total_size, int) and total_size >= 0, "total_size must be a non-negative integer"
        assert isinstance(downloaded, int) and downloaded >= 0, "downloaded must be a non-negative integer"
        assert isinstance(uploaded, int) and uploaded >= 0, "uploaded must be a non-negative integer"
        assert left is None or (isinstance(left, int) and left >= 0), "left must be a non-negative integer or None"
        
        self.info_hash = info_hash
        self.total_size = total_size
        self.uploaded = uploaded
        self.downloaded = downloaded
        cal_left = max(self.total_size - self.downloaded, 0)
        self.left = cal_left if left is None else left
        self.event = event   # Default tracker event
        
        self.peers: dict[tuple[str, int], dict] = {}  # List of (ip, port) tuples
        self.peers6: dict[tuple[str, int], dict] = {} # List of (ip, port) tuples for IPv6

    def update_uploaded(self, bytes_uploaded: int):
        self.uploaded += bytes_uploaded

    def update_downloaded(self, bytes_downloaded: int):
        self.downloaded += bytes_downloaded
        self.left = max(self.total_size - self.downloaded, 0)

    def set_event(self, event: TorrentStatus):
        self.event = event
