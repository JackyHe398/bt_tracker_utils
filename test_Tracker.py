from  torrentlib import Tracker, TorrentStatus, Torrent
from random import choice, sample

def test_multiple_trackers_check():
    # Test tracker checking
    with open("trackers.txt", "r") as f:
        urls = list(line.strip() for line in f if line.strip() and not line.startswith("#"))

    result = Tracker.Check.multiple(urls, timeout=5)
    print(result)

    result = Tracker.Check.auto("udp://tracker.torrent.eu.org:451/announce")
    print(result)

def test_tracker_query():
    # Test tracker querying
    torrent = Torrent("95eac181669f6e2e26a2513f9b2c9f6d3d4e0ec1", 0)
    self_peer_id = "-robots-testing12345"
    for tracker_url in ('https://tracker.ghostchu-services.top:443/announce',
                        'udp://tracker.torrent.eu.org:451/announce',
                        'http://tracker.opentrackr.org:1337/announce'):
        try:
            result = Tracker.Query.single(torrent, tracker_url, self_peer_id)
            print(result)
        except Exception as e:
            print(f"Error querying tracker {tracker_url}: {e}")
            
    print(f"Total peers obtained: {len(torrent.peers)}")
    
if __name__ == "__main__":
    test_multiple_trackers_check()
    test_tracker_query()