import requests
import struct
import random
import socket
from enum import Enum
import bencodepy as bec
from typing import Dict, Any
from urllib.parse import urlparse
from .TrackerQueryException import (
    TrackerQueryException,
    TimeoutError,
    BadRequestError, 
    InvalidResponseError,
    UnexpectedError
)

# example_hash = '8a19577fb5f690970ca43a57ff1011ae202244b8'
# example_peer_id = '-robots-testing12345'
class TrackerEvent(Enum):
    NONE = 0
    COMPLETED = 1
    STARTED = 2
    STOPPED = 3


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


class Query:
    @staticmethod
    def http(url: str,
            info_hash: str,
            peer_id: str,
            event: str,
            left: int = 0, downloaded: int = 0, uploaded: int = 0,
            ip_addr: str|None = None,
            num_want: int|None = None, key: int = 0,
            port: int = 6881, headers: dict|None = None,
            timeout: int = 5) -> Dict[str, Any]:
        """
        Check if a given HTTP URL is reachable and returns a status code.
        """
        info_hash_bytes = bytes.fromhex(info_hash)

        headers = headers or {
            "User-Agent": "qBittorrent/4.5.2",  # Mimic a known client
            "Accept": "*/*",
            "Connection": "close"
        }

        params = {
            'info_hash': info_hash_bytes,
            'peer_id': peer_id,
            'port': str(port),
            'left': str(left or 0),
            'downloaded': str(downloaded or 0),
            'uploaded': str(uploaded or 0),
            'event': event,
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
                response_bdecode = dict(bec.decode(response.content))
                response_bdecode[b"peers"] = _get_peer_from_bytes(response_bdecode[b"peers"])
                if b"peers6" in response_bdecode:
                    response_bdecode[b"peers6"] = _get_peer6_from_bytes(response_bdecode[b"peers6"])
                response_decoded = {k.decode(): (v.decode() if isinstance(v, bytes) else v) for k, v in response_bdecode.items()}
                return _format_result(response_decoded)
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
    def udp(url: str,
            info_hash: str,
            peer_id: str,
            event: TrackerEvent|int,
            left: int = 0, downloaded: int = 0, uploaded: int = 0,
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
        
        if isinstance(event, TrackerEvent):
            event = event.value

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
                bytes.fromhex(info_hash),
                peer_id.encode("utf-8")[:20].ljust(20, b"-"),
                downloaded or 0,
                left or 0,
                uploaded or 0,
                event,
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

def query(url: str,
            info_hash: str,
            peer_id: str,  
            event: TrackerEvent, 
            left = 0, downloaded = 0, uploaded = 0, 
            ip_addr: str|None = None,
            num_want = None, key = None,
            port: int|None = None, headers = None,
            timeout: int = 5) -> Dict[str, Any]:

    # region - arguement preparing
    args: Dict[str, Any] = {
        "url": url,
        "info_hash": info_hash,
        "peer_id": peer_id,
    }

    if left is not None: args["left"] = left
    if downloaded is not None: args["downloaded"] = downloaded
    if uploaded is not None: args["uploaded"] = uploaded
    if ip_addr is not None: args["ip_addr"] = ip_addr
    if num_want is not None: args["num_want"] = num_want
    if key is not None: args["key"] = key
    if port is not None: args["port"] = port
    if headers is not None: args["headers"] = headers
    if timeout is not None: args["timeout"] = timeout
    # endregion
        
    if url.startswith("http"):
        args["event"] = event.name.lower()
        return Query.http(**args)
    elif url.startswith("udp"):
        args["event"] = event.value
        return Query.udp(**args)
    else:
        raise TrackerQueryException(message="Unsupported URL scheme", url=url)