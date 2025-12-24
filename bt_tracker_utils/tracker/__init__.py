"""
BitTorrent Tracker Utilities

A Python library for checking tracker availability and querying tracker information.
"""

from .Check import Check
from .Query import Query
from ..Torrent import TorrentStatus

__version__ = "1.0.0"
__author__ = "JackyHe398"
__email__ = "your-email@example.com"  # Optional
__description__ = "BitTorrent tracker utilities for checking availability and querying"

# Define what gets imported with "from bt_tracker_utils import *"
__all__ = [
    "TorrentStatus",
    "Query",
    "Check",
]