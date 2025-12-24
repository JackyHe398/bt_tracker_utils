# BT_TRACKER_UTILS

**This library is currently under developement, it may change rapidly. Please use with care**

## Introduction

This is a utility library for checking tracker status and querying tracker in different protocols.

## Features

- **Check Tracker Status**: Verify if a tracker is online and responsive.
- **Concurrent Queries**: Perform multiple tracker queries simultaneously.
- **UDP and HTTP Protocols**: Support for both UDP and HTTP tracker protocols.
- **Full Param Support**: Allows for full parameter customization in tracker queries.

## Installation

```
pip install bt-tracker-utils
```

## Usage Example - Check status

```python
from bt_tracker_utils import check_trackers, check_tracker, CheckTracker
timeout = 5  # seconds

# Check single tracker
CheckTracker.udp("udp://tracker.example.com:8080/announce", timeout=timeout)
CheckTracker.http("http://tracker.example.com:8080/announce", timeout=timeout)

check_tracker("http://tracker.example.com:8080/announce", timeout=timeout) # smart checking, identifies protocol automatically

 
# Check multiple trackers
with open("trackers.txt", "r") as f:
    urls = []
    for line in f:
        line = line.strip()
        urls.append(line)
check_trackers(urls, timeout=timeout)
```

## Usage Example - Query Tracker:

```python
import bt_tracker_utils as bt

seed = "8a19577fb5f690970ca43a57ff1011ae202244b8"
peer_id = "-robots-testing12345"

# specifying protocols
bt.Query.udp(seed, "udp://tracker.torrent.eu.org:451/announce",
         peer_id, bt.TrackerEvent.STARTED,
         ip_addr = "66.35.68.60", port = 6885)

bt.Query.http(seed, "http://tracker.opentrackr.org:1337/announce",
         peer_id, bt.TrackerEvent.STOPPED, timeout = 5,
         num_want = 100, key = "0327")

# Smart query with auto-detection
bt.Query.single(seed, "udp://tracker.torrent.eu.org:451/announce",
         peer_id, bt.TrackerEvent.STARTED,
         ip_addr = "66.35.68.60", port = 6885)

bt.Query.single(seed, "http://nyaa.tracker.wf:7777/announce",
      peer_id, bt.TrackerEvent.NONE,
      left = 1145141919810, downloaded = 0, uploaded = 1048576)
```

### Full parameters

```python
class query
    def single(info_hash: str,
              url: str,  
              peer_id: str,  
              event: TrackerEvent, 
              left = 0, downloaded = 0, uploaded = 0, 
              ip_addr: str|None = None,
              num_want = None, key = None,
              port: int|None = None, headers = None,
              timeout: int = 5) -> Dict[str, Any]:
```

#### Force:

- `info_hash`: A 20-byte info hash of the torrent.
- `peer_id`: A 20-byte peer ID of the client.
- `event`(type: `TrackerEvent`): The status of download (`NONE`, `STARTED`, `STOPPED`, `COMPLETED`).

#### Recommended:

- `left`: The number of bytes left to download.
- `downloaded`: The number of bytes downloaded.
- `uploaded`: The number of bytes uploaded.
- `ip_addr`: The IP address of the client (for UDP).
- `port`: The port number of the client (for UDP).

#### Optional:

- `num_want`: The number of peers to return (default: 50).
- `key`: A unique key for the request. Tracker can use this to recognize the client even if a different machine is used.
- `headers`: Additional HTTP headers for the request. If UDP is used, this field will be ignored.
- `timeout`: The timeout for the request in seconds (default: 5s).

### Return Values:

The query function returns a dictionary containing the following. Note that values can be `None`(for required fields) or not present(for optional fields) if the response does not contain that field:

#### Optional fields:

- `failure reason`: If this field is present, all the other fields will not exist.
- `warning message`: This field do not affect the other fields.

#### Required fields:

- `interval`: The interval in seconds for the next query.
- `min interval`: The minimum interval in seconds for the next query, query should not be made more frequently than this.
- `leechers`: The number of peers currently downloading the torrent.
- `seeders`: The number of peers currently seeding the torrent.
- `peers`: A list of tuple, storing (ip, port) for each peer.
- `peers6`: A list of tuple, storing (ip, port) for each peer in IPv6 format.

## Error Handling

The library raises specific exceptions for different error conditions:

```python
from bt_tracker_utils import query, TrackerEvent, TrackerQueryException

try:
    result = query(url, info_hash, peer_id, TrackerEvent.STARTED)
except TrackerQueryException as e:
    print(f"Tracker error: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

### Exception Types

- `TimeoutError`: Request timed out
- `BadRequestError`: Invalid request parameters
- `InvalidResponseError`: Malformed tracker response
- `UnexpectedError`: Network or other unexpected errors

## References and Further Reading

[Wikipedia](https://en.wikipedia.org/wiki/BitTorrent_tracker)

[CSDN](https://blog.csdn.net/zyd_15221378768/article/details/79785075)

[Theory Wiki](https://wiki.theory.org/BitTorrent_Tracker_Protocol)

[Concurrency Deep Dives](https://concurrencydeepdives.com/udp-tracker-protocol/)

[XBTT](https://xbtt.sourceforge.net/udp_tracker_protocol.html)

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

Created by JackyHe398 © 2025
