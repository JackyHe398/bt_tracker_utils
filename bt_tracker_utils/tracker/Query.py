import requests
import struct
import random
import socket
import bencodepy as bec
from typing import Dict, Any
from urllib.parse import urlparse

from ..Torrent import Torrent, TorrentStatus
from .TrackerQueryException import (
    TrackerQueryException,
    TimeoutError,
    BadRequestError, 
    InvalidResponseError,
    UnexpectedError
)

# example_hash = '8a19577fb5f690970ca43a57ff1011ae202244b8'
# example_peer_id = '-robots-testing12345'


def _get_peer_from_bytes(response: bytes, result: list[tuple] = []) -> list[tuple]:
    """
    Extracts peer information from the UDP response.
    """
    if len(response) <6:
        return result
    peer_bytes = response[:6]
    ip_packed, port = struct.unpack("!4sH", peer_bytes)
    ip = socket.inet_ntoa(ip_packed)
    result.append((ip, port))
    return _get_peer_from_bytes(response[6:], result)

def _get_peer6_from_bytes(response: bytes, result: list[tuple] = []) -> list[tuple]:
    """
    Extracts peer information from the UDP response for IPv6.
    """
    if len(response) < 18:
        return result
    peer_bytes = response[:18]
    ip_packed, port = struct.unpack("!16sH", peer_bytes)
    ip = socket.inet_ntop(socket.AF_INET6, ip_packed)
    result.append((ip, port))
    return _get_peer6_from_bytes(response[18:], result)

def _udp_response_parser(response: bytes) -> Dict[str, Any]:
    """
    Parses the UDP response from the tracker.
    """
    result = {}

    header = response[:20]
    peer_bytes = response[20:]

    action, transaction_id, result["interval"], result["leechers"], result["seeder"] = struct.unpack("!iiiii", header)
    if action != 1 and transaction_id != 0:
        raise InvalidResponseError(message=f"Invalid action or transaction ID, action id: {action}, transaction id: {transaction_id}")

    result["peers"] = _get_peer_from_bytes(peer_bytes)
    return result


def _format_result(result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Formats the result from the tracker query into a human-readable string.
    """

    if "failure reason" in result:
        return result 
    formatted = {
        "interval": None,
        "min interval": None,
        "leechers": None,
        "seeders": None,
        "peers": None,
        "peers6": None
    }

    if "complete" in result:
        formatted["seeders"] = result["complete"]
        result.pop("complete")
    if "incomplete" in result:
        formatted["leechers"] = result["incomplete"]
        result.pop("incomplete")
    
    for key, value in result.items():
        formatted[key] = value
    return formatted

def _decode_ip(response: dict[bytes, Any]) -> Dict[str, Any]:
    """
    Decodes the response from the tracker.
    """

    response[b"peers"] = _get_peer_from_bytes(response[b"peers"])
    if b"peers6" in response:
        response[b"peers6"] = _get_peer6_from_bytes(response[b"peers6"])


    response_decoded = {}
    for k, v in response.items():
        if b'ip' in k: # if the key contains 'ip', decode with inet_ntoa
            # Check if it's IPv4 (4 bytes) or IPv6 (16 bytes)
            if len(response[k]) == 4:
                v = socket.inet_ntoa(response[k])
            elif len(response[k]) == 16:
                v = socket.inet_ntop(socket.AF_INET6, response[k])
            else:
                v = response[k]
        try: 
            response_decoded[k.decode()] = (v.decode() if isinstance(v, bytes) else v)
        except:
            response_decoded[k.decode()] = v

    return response_decoded

class Query:
    @staticmethod
    def http(torrent: Torrent,
            url: str,
            peer_id: str,
            ip_addr: str|None = None,
            num_want: int|None = None, key: int = 0,
            port: int = 6881, headers: dict|None = None,
            timeout: int = 5) -> Dict[str, Any]:
        """
        Check if a given HTTP URL is reachable and returns a status code.
        """
        
        info_hash_bytes = bytes.fromhex(torrent.info_hash)

        headers = headers or {
            "User-Agent": "qBittorrent/4.5.2",  # Mimic a known client
            "Accept": "*/*",
            "Connection": "close"
        }

        params = {
            'info_hash': info_hash_bytes,
            'peer_id': peer_id,
            'port': str(port),
            'left': str(torrent.left),
            'downloaded': str(torrent.downloaded),
            'uploaded': str(torrent.uploaded),
            'event': torrent.event.name.lower(), # Convert TorrentStatus to string
        }

        if ip_addr: params['ip'] = ip_addr
        if num_want: params['numwant'] = str(num_want)
        if key: params['key'] = str(key)

        try:
            response = requests.get(url,
                                    headers=headers,
                                    params=params,
                                    allow_redirects=True,
                                    timeout=timeout)
            status_code = response.status_code//100*100  # Get the first digit of the status code
            if status_code == 200:
                response_bdecode: dict[bytes, bytes] = dict(bec.decode(response.content))
                response_decode = _decode_ip(response_bdecode)
                return _format_result(response_decode)
            elif status_code == 300:
                raise UnexpectedError(url=url, message="Redirection not supported")
            elif status_code == 400:
                raise BadRequestError(url=url)
            else:
                raise InvalidResponseError(url=url)
        except requests.exceptions.Timeout:
            raise TimeoutError(url=url)
        except requests.exceptions.RequestException as e:
            raise UnexpectedError(url=url, e=e)


    @staticmethod
    def udp(torrent: Torrent,
            url: str,
            peer_id: str,
            ip_addr: str = "0.0.0.0",
            num_want: int = 50, key: int = 0,
            port: int = 6881,
            timeout: int = 5)  -> Dict[str, Any]:
        def initializing_validator(response) -> Dict[str, Any]:
            """
            Validates the response from the tracker during initialization.
            """
            action, transaction_id, connection_id = struct.unpack("!iiq", response[:16])
            if action == 0 and transaction_id == TRANSACTION_ID:
                return connection_id
            else:
                raise InvalidResponseError(url=url)

        # region - define constants and params
        parsed = urlparse(url)
        HOSTNAME = parsed.hostname
        PORT = parsed.port

        PROTOCOL_ID = 0x41727101980    # 8-byte magic number
        TRANSACTION_ID = random.randint(0, 0xFFFF)  # Random 4-byte integer
        
        ip_bytes = socket.inet_aton(ip_addr)
        # endregion


        # Create packet: ! means network byte order (big-endian)

        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(timeout)

        try:
            # region - initialize connection
            packet = struct.pack("!qii", PROTOCOL_ID, 0, TRANSACTION_ID) # ACTION: connect
            s.sendto(packet, (HOSTNAME, PORT))
            response, addr = s.recvfrom(1024)  # buffer size can be adjusted
            # You can unpack the response here depending on expected format
            CONNECTION_ID = initializing_validator(response)
            # endregion

            # region - query
            packet = struct.pack(
                "!qii20s20sqqqi4siiH",
                CONNECTION_ID,
                1,  # ACTION: announce
                TRANSACTION_ID,
                bytes.fromhex(torrent.info_hash),
                peer_id.encode("utf-8")[:20].ljust(20, b"-"),
                torrent.downloaded,
                torrent.left,
                torrent.uploaded,
                torrent.event.value, # Convert TorrentStatus to int
                ip_bytes,
                key,
                num_want,
                port or 6881
            )
            s.sendto(packet, (HOSTNAME, PORT))
            response, addr = s.recvfrom(1024)  # buffer size can be adjusted
            # endregion
        except socket.timeout:
            raise TimeoutError(url=url)
        except socket.error as e:
            raise UnexpectedError(url=url, e=e)
        finally:
            s.close()
        
        return _format_result(_udp_response_parser(response))

    @staticmethod
    def single(torrent: Torrent,
                url: str,
                peer_id: str,  
                ip_addr: str|None = None,
                num_want = None, key = None,
                port: int|None = None, headers = None,
                timeout: int|None = None) -> Dict[str, Any]:

        # region - arguement preparing
        args: Dict[str, Any] = {
            "torrent": torrent,
            "url": url,
            "peer_id": peer_id
        }

        if ip_addr is not None: args["ip_addr"] = ip_addr
        if num_want is not None: args["num_want"] = num_want
        if key is not None: args["key"] = key
        if port is not None: args["port"] = port
        if timeout is not None: args["timeout"] = timeout
        # endregion
            
        if url.startswith("http"):
            if headers is not None: args["headers"] = headers
            return Query.http(**args)
        elif url.startswith("udp"):
            return Query.udp(**args)
        else:
            raise TrackerQueryException(message="Unsupported URL scheme", url=url)
    
    @staticmethod
    def multi(torrent: Torrent,
                urls: list[str],
                peer_id: str,  
                ip_addr: str|None = None,
                num_want = None, key = None,
                port: int|None = None, headers = None,
                timeout: int|None = None, max_threads: int = 50) -> Dict[str, Dict[str, Any]]:
        import threading
        semaphore = threading.Semaphore(max_threads)
        result = {}
        threads = []  # Keep track of threads
        
        def threaded_check(url):
            with semaphore:
                try:
                    result[url] = Query.single(torrent, url, peer_id,
                                       ip_addr=ip_addr,
                                       num_want=num_want, key=key, port=port, headers=headers, timeout=timeout)
                except Exception as e:
                    result[url] = {"error": str(e)}  # Store error in result instead of printing

        for url in urls:
            threaded = threading.Thread(target=threaded_check, args=(url,))
            threaded.start()
            threads.append(threaded)  # Keep track of the thread
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
            
        return result