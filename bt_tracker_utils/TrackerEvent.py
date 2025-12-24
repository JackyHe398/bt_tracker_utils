from enum import Enum

class TrackerEvent(Enum):
    STARTED = "started"
    COMPLETED = "completed"
    STOPPED = "stopped"