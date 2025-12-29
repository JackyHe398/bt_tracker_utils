import io
import json
from  torrentlib import Peer, TorrentStatus, Torrent
from torrent_parser import TorrentFileParser
from time import sleep
from datetime import datetime, timedelta

# Test Peer class initialization
torrent = Torrent("95eac181669f6e2e26a2513f9b2c9f6d3d4e0ec1", 0)
self_peer_id = "-robots-testing12345"
peer = Peer(('192.168.0.150', 50413), torrent, self_peer_id)
print(torrent)

try:
    peer.connect()
    print(f"Connected to peer")
    print(f"Peer support extensions: {peer.peer_supports_extensions}")
    print(f"Peer extensions IDs: {peer.peer_extension_ids}")
    
    timeout = datetime.now() + timedelta(minutes=2)
    while datetime.now() < timeout and not torrent.peers:
        peer.read_all()
        sleep(10)
        print(torrent.peers)
        print(torrent.peers6)
    
    print("\n\n\nRequesting metadata...")
    peer.request_all_metadata()
    if torrent.metadata:
        f = io.BytesIO(torrent.metadata)
        meta_dict = TorrentFileParser(f).parse()
    else:
        print("No metadata received from peer.")
        
finally:
    peer.close()
    
print(torrent)