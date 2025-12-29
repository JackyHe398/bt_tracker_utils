# torrentlib

**This library is currently under development, it may change rapidly. Please use with care**

## Introduction

torrentlib is a Python library for torrent information retrieval (peers and metadata), providing tools for tracker communication, peer protocol implementation, and torrent metadata handling. This library aims to facilitate the development of BitTorrent clients and related applications by offering a modular and easy-to-use interface, while not being a full-fledged BitTorrent client itself. Hence, it does not handle downloading or uploading of torrent data other than metadata.

#### Important Notice:
**Please do not use this library for leeching.** This library is intended for legitimate purposes such as:
- Checking tracker health and availability
- Analyzing torrent metadata
- Building torrent clients that properly seed content back to the community
- Educational purposes to understand BitTorrent protocols

BitTorrent networks thrive on reciprocity. If you download content, please contribute back by seeding. Leeching (downloading without seeding) degrades the network for everyone and violates the spirit of peer-to-peer file sharing.

## Features

### Torrent Management

- Parse .torrent files
- Torrent metadata handling
- File information extraction

### Peer Discovery

- Query trackers over UDP and HTTP protocols
- Support for full parameter customization
- Peer Exchange (PEX) support - exchange peer lists with connected peers

### Metadata management

- Retrieve torrent metadata from peers using the BitTorrent Extension Protocol (BEP 9)
- Thread-safe peer and metadata management for concurrent operations

### Tracker Operations

- Check Tracker Status - Verify if tracker(s) is online and responsive


## Installation

```bash
pip install torrentlib
```

## Usage

### Working with Torrents

Other than checking tracker status, a Torrent object is needed for queries. This is the foundation for tracker queries and peer communication. There are two main ways to create a Torrent object: loading from a .torrent file or creating a minimal torrent using just the info_hash. Torrent objects created from both methods can be used interchangeably.

Loading from a .torrent file:
```python
from torrentlib import Torrent

# Load from .torrent file
torrent = Torrent.from_file(filename="example.torrent")

print(torrent)  # Human-readable representation
# Output: Torrent('example.iso', hash=3b245504c0e113..., size=5.7 GiB, progress=0.0%, peers=0)

print(f"Name: {torrent.name}")
print(f"Info hash: {torrent.info_hash}")
print(f"Total size: {torrent.total_size} bytes")
print(f"Pieces: {torrent.num_pieces}")
print(f"Piece length: {torrent.piece_length}")

# Access file information
files = torrent.get_files()
for file_hash, file_info in files.items():
    print(f"File: {file_info['name']}, Size: {file_info['length']} bytes")
```

Creating a minimal torrent using just the info_hash:
```python
from torrentlib import Torrent, TorrentStatus

# Create minimal torrent from info_hash (useful for magnet links or metadata downloads)
torrent = Torrent(
    info_hash="1234567890abcdef1234567890abcdef12345678"
)

# or provide additional information
torrent = Torrent(
    info_hash="1234567890abcdef1234567890abcdef12345678",
    total_size = 1145141919810, left = 1145141919810,
    downloaded = 0, uploaded = 0,
    event = TorrentStatus.STOPPED,
    name = "example_file.iso",
    piece_length = None,
    num_pieces = None
)
```

### Tracker Status Checking

Torrent status check is to reduce the size of tracker lists by filtering out offline or unresponsive trackers for efficient querying. Large unfunctioning tracker can degrade performance and waste resources for a bittorrent client.
You can check single or multiple trackers, with automatic protocol detection (HTTP/HTTPS or UDP) or by specifying the protocol explicitly.

```python
from torrentlib.Tracker import Check

# Check single tracker with auto-detection
Check.single("http://tracker.example.com:8080/announce", timeout=5)
Check.single("udp://tracker.example.com:8080/announce", timeout=5)

# Or specify protocol explicitly
Check.http("http://tracker.example.com:8080/announce", timeout=5)
Check.udp("udp://tracker.example.com:8080/announce", timeout=5)

# Check multiple trackers concurrently
trackers = [
    "http://tracker1.example.com:8080/announce",
    "udp://tracker2.example.com:6969/announce",
]
results = Check.multiple(trackers, timeout=5)
for url, status in results.items():
    print(f"{url}: {'✓' if status else '✗'}")
```

### Tracker Queries

Once you have a Torrent object, query trackers to get peer lists. We strongly recommend wrapping the query calls in try-except blocks to handle potential exceptions gracefully since network operations can be unreliable.:

```python
from torrentlib import Torrent, TorrentStatus
from torrentlib.Tracker import Query

# Basic query with auto-protocol detection
response = Query.single(
    info_hash=torrent.info_hash,
    url="udp://tracker.opentrackr.org:1337/announce",
    peer_id=peer_id,
    event=TorrentStatus.STARTED,
    port=6881
)

# Full parameter query
response = Query.single(
    info_hash=torrent.info_hash,
    url="http://tracker.example.com:8080/announce",
    peer_id=peer_id,
    event=TorrentStatus.STARTED,
    left=torrent.left,           # Use torrent's actual values
    downloaded=torrent.downloaded,
    uploaded=torrent.uploaded,
    port=6881,
    num_want=50,           # Number of peers wanted
    timeout=10
)

print(f"Interval: {response['interval']}s")
print(f"Seeders: {response.get('seeders', 0)}")
print(f"Leechers: {response.get('leechers', 0)}")
print(f"Peers: {len(response.get('peers', []))}")

# Store peers in torrent object
for ip, port in response.get('peers', []):
    torrent.peers[(ip, port)] = {}
```

### Peer Communication

Connect to peers to exchange metadata and peer lists using the BitTorrent peer protocol. PEX data is exchanged automatically when connected to a peer that supports it, no request is needed or can speed it up. Keep-alive messages must be sent manually to maintain long-running connections:

```python
from torrentlib import Torrent, Peer
from time import sleep

with Peer(peer_addr, torrent, peer_id) as peer:
    print(f"Connected: {peer}")
    print(f"Supports extensions: {peer.peer_supports_extensions}")
    print(f"Extension IDs: {peer.peer_extension_ids}")
    
    # Exchange peer lists via PEX (Peer Exchange)
    # Automatically happens when reading messages
    sleep(20)  # Wait to receive PEX messages
    peer.read_all()
    
    print(f"Discovered peers: {len(torrent.peers)}")
    for (ip, port), metadata in torrent.peers.items():
        print(f"  {ip}:{port} - {metadata}")
```

#### Maintaining Long Connections with Keep-Alive

For long-running connections, send keep-alive messages periodically to prevent timeouts:

```python
import threading
from time import sleep
from torrentlib import Peer
from torrentlib.PeerCommunicationExceptions import SocketClosedException

def keep_alive_loop(peer: Peer, interval: int = 120, stop_event: threading.Event = None):
    """
    Send keep-alive messages periodically.
    
    Args:
        peer: Peer object to send keep-alive to
        interval: Seconds between keep-alive messages (default: 120)
        stop_event: Optional event to signal thread to stop
    """
    while not (stop_event and stop_event.is_set()):
        try:
            sleep(interval)
            peer.send_keep_alive()
            print(f"Keep-alive sent to {peer.peer}")
        except SocketClosedException:
            print(f"Connection closed to {peer.peer}, exiting keep-alive loop")
            break
        except Exception as e:
            print(f"Error sending keep-alive: {e}")
            break

try:
    with Peer(peer_addr, torrent, peer_id) as peer:
        # Start keep-alive thread
        keep_alive_thread = threading.Thread(
            target=keep_alive_loop,
            args=(peer, 120, stop_event),
            daemon=True
        )
        keep_alive_thread.start()
        
        # Do your work with the peer
        peer.read_all()
        sleep(300)  # Keep connection for 5 minutes
        
finally:
    # Signal thread to stop
    stop_event.set()
```

### Metadata Download (BEP 9)

Download torrent metadata from peers when you only have the info_hash (e.g., from magnet links):

```python
with Peer(peer_addr, torrent, peer_id) as peer:
    # Request all metadata pieces
    peer.request_all_metadata()
    
    # Read responses
    peer.read_all()
    
    # Metadata is automatically assembled and verified
    if torrent.metadata:
        print("Metadata downloaded successfully!")
        print(torrent)  # Now shows complete info
        print(f"Name: {torrent.name}")
        print(f"Size: {torrent.total_size} bytes")
        print(f"Pieces: {torrent.num_pieces}")
        
        # Access files
        files = torrent.get_files()
        for file_hash, file_info in files.items():
            print(f"  {file_info['name']}: {file_info['length']} bytes")
    else:
        print("Failed to download metadata")
```

### Complete Example: Magnet Link to File List

```python
response = Query.single(
    info_hash=info_hash,
    url=tracker_url,
    peer_id=peer_id,
    event=TorrentStatus.STARTED,
    port=6881
)

print(f"Found {len(response.get('peers', []))} peers")

# 4. Try to get metadata from first peer
for ip, port in response.get('peers', [])[:5]:  # Try first 5 peers
    try:
        with Peer((ip, port), torrent, peer_id) as peer:
            peer.request_all_metadata()
            
            if torrent.metadata:
                print(f"\n✓ Got metadata from {ip}:{port}")
                print(torrent)
                
                # List all files
                files = torrent.get_files()
                if files:
                    print(f"\nFiles ({len(files)}):")
                    for file_hash, file_info in files.items():
                        print(f"  - {file_info['name']} ({file_info['length']} bytes)")
                break
    except Exception as e:
        print(f"✗ Failed to connect to {ip}:{port}: {e}")
        continue
else:
    print("Could not download metadata from any peer")
```

## API Reference

### Tracker Query Parameters

#### Required:
- `info_hash` (str): 40-character hex string of the torrent's info hash
- `peer_id` (str): 20-character client peer ID
- `event` (TorrentStatus): Download status - `STARTED`, `STOPPED`, `COMPLETED`, or `NONE`

#### Recommended:

- `left` (int): Bytes remaining to download
- `downloaded` (int): Total bytes downloaded
- `uploaded` (int): Total bytes uploaded
- `port` (int): Client's listening port (required for UDP)

#### Optional:

- `num_want` (int): Number of peers requested (default: 50)
- `ip_addr` (str): Client's IP address (for UDP)
- `key` (str): Unique key for tracker recognition
- `timeout` (int): Request timeout in seconds (default: 5)
- `headers` (dict): Additional HTTP headers (HTTP only)

### Tracker Response Fields

#### Success Response:

- `interval` (int): Seconds until next announce
- `min interval` (int): Minimum announce interval
- `seeders` (int): Number of seeders
- `leechers` (int): Number of leechers
- `peers` (list): List of (ip, port) tuples (IPv4)
- `peers6` (list): List of (ip, port) tuples (IPv6)

#### Error Response:

- `failure reason` (str): Error message from tracker
- `warning message` (str): Optional warning (doesn't affect other fields)

## Error Handling

```python
from torrentlib.Tracker import Query, TrackerQueryException
from torrentlib import TorrentStatus

try:
    response = Query.single(
        info_hash="...",
        url="http://tracker.example.com/announce",
        peer_id="...",
        event=TorrentStatus.STARTED
    )
except TrackerQueryException as e:
    print(f"Tracker error: {e}")
except TimeoutError:
    print("Request timed out")
except Exception as e:
    print(f"Unexpected error: {e}")
```

### Exception Types
#### TrackerQueryException Subclasses:
- `TrackerQueryException`: Base exception for tracker-related errors
- `TimeoutError`: Request exceeded timeout
- `BadRequestError`: Invalid request parameters
- `InvalidResponseException`: Malformed tracker response
- `UnexpectedError`: Network or other unexpected errors

#### PeerCommunicationExceptions Subclasses:
- `PeerCommunicationException`: Base exception for peer communication errors
- `SocketClosedException`: Connection loss from peer. Rehandshake needed.
- `InvalidResponseException`: Malformed peer response or unexpected/unsupported message

## References and Further Reading

[Wikipedia](https://en.wikipedia.org/wiki/BitTorrent_tracker)

[CSDN](https://blog.csdn.net/zyd_15221378768/article/details/79785075)

[Theory Wiki](https://wiki.theory.org/BitTorrent_Tracker_Protocol)

[Concurrency Deep Dives](https://concurrencydeepdives.com/udp-tracker-protocol/)

[XBTT](https://xbtt.sourceforge.net/udp_tracker_protocol.html)


## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

Created by JackyHe398 © 2025
