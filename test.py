from bt_tracker_utils import Tracker, TorrentStatus, Torrent
from random import choice, sample

# Test tracker checking
with open("trackers.txt", "r") as f:
    urls = list(line.strip() for line in f if line.strip() and not line.startswith("#"))

result = tracker.Check.multiple(urls, timeout=5)
print(result)

result = tracker.Check.auto("udp://tracker.torrent.eu.org:451/announce")
print(result)

# Test tracker querying
torrent = Torrent("b547cdccd2f6248e4d76cb3d7a9012cfe3fee2da", 0)
self_peer_id = "-robots-testing12345"
for tracker_url in ('https://tracker.ghostchu-services.top:443/announce',
                    'udp://tracker.torrent.eu.org:451/announce',
                    'http://tracker.opentrackr.org:1337/announce'):
    try:
        result =tracker.Query.single(torrent, tracker_url, self_peer_id)
        print(result)
    except Exception as e:
        print(f"Error querying tracker {tracker_url}: {e}")
