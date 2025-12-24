# from bt_tracker_utils import CheckTracker, check_trackers, TrackerEvent, check_tracker, Query

# result = query("udp://tracker.torrent.eu.org:451/announce",
#           "b547cdccd2f6248e4d76cb3d7a9012cfe3fee2da",
#           "-robots-testing12345",
#           TrackerEvent.STOPPED)

# print(result)

# result = Query.http("http://tracker.opentrackr.org:1337/announce",
#           "8a19577fb5f690970ca43a57ff1011ae202244b8",
#           "-robots-testing12345",
#           TrackerEvent.STOPPED)

# print(result)

# check_tracker("udp://tracker.torrent.eu.org:451/announce")

from bt_tracker_utils import tracker, TrackerEvent
from random import choice, sample


with open("trackers.txt", "r") as f:
    urls = list(line.strip() for line in f if line.strip() and not line.startswith("#"))


result = tracker.Query.single("b547cdccd2f6248e4d76cb3d7a9012cfe3fee2da", 'https://tracker.ghostchu-services.top:443/announce',
            "-robots-testing12345",
            TrackerEvent.STOPPED)

print(result)