"""
BitTorrent Tracker Utilities

A Python library for checking tracker availability and querying tracker information.
"""

from .check_tracker import CheckTracker, check_trackers, check_tracker
from .query import TrackerEvent, query, Query

__version__ = "1.0.0"
__author__ = "JackyHe398"
__email__ = "your-email@example.com"  # Optional
__description__ = "BitTorrent tracker utilities for checking availability and querying"

# Define what gets imported with "from bt_tracker_utils import *"
__all__ = [
    "CheckTracker",
    "check_trackers", 
    "check_tracker",
    "TrackerEvent",
    "query"
]