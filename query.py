import requests
import struct
import random
import socket
import bencodepy as bec
from typing import Dict, Any
from urllib.parse import urlparse
import TrackerQueryException as TQError

# example_hash = '8a19577fb5f690970ca43a57ff1011ae202244b8'
# example_peer_id = '-robots-testing12345'

def udp_response_parser(response: bytes) -> Dict[str, Any]:
    def get_peer_from_bytes(response: bytes, result: list[str] = []) -> list[str]:
        """
        Extracts peer information from the UDP response.
        """
        if len(response) <6:
            return result
        peer_bytes = response[:6]
        ip_packed, port = struct.unpack("!4sH", peer_bytes)
        ip = socket.inet_ntoa(ip_packed)
        result.append((ip, port))
        return get_peer_from_bytes(response[6:], result)


    """
    Parses the UDP response from the tracker.
    """
    result = {}

    header = response[:20]
    peer_bytes = response[20:]

    action, transaction_id, result["interval"], result["leechers"], result["seeder"] = struct.unpack("!iiiii", header)
    if action != 1 and transaction_id != 0:
        raise TQError.InvalidResponseError(message="Invalid action or transaction ID")
    
    result["peers"] = get_peer_from_bytes(peer_bytes)
    return result


class Query:
    def http(url: str,
            info_hash: str,
            peer_id: str,  
            event: str, 
            left = 0, downloaded = 0, uploaded = 0, 
            port:int = 6881, headers = None ) -> Dict[str, Any]:
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

        try:
            response = requests.get(url,
                                    headers=headers,
                                    params=params,
                                    allow_redirects=True,
                                    timeout=5)
            status_code = response.status_code//100*100  # Get the first digit of the status code
            if status_code == 200:
                response_result = bec.decode(response.text)
                return response_result
            elif status_code == 300:
                raise TQError.UnexpectedError(url=url, message="Redirection not supported")
            elif status_code == 400:
                raise TQError.BadRequestError(url=url)
            else:
                raise TQError.InvalidResponseError(url=url)
        except requests.exceptions.Timeout as e:
            raise TQError.TimeoutError(url=url, e=e)
        except requests.exceptions.RequestException as e:
            raise TQError.UnexpectedError(url=url, e=e)


    def udp(url: str,
            info_hash: str,
            peer_id: str,  
            event: int, 
            left = 0, downloaded = 0, uploaded = 0, 
            ip_addr:str = "0.0.0.0",
            num_want = 50, key = random.randint(0, 0xFFFF),
            port:int = 6881) -> bool:
        def initializing_validator(response)-> int:
            """
            Validates the response from the tracker during initialization.
            """
            action, transaction_id, connection_id = struct.unpack("!iiq", response[:16])
            if action == 0 and transaction_id == TRANSACTION_ID:
                return connection_id
            else:
                raise TQError.InvalidResponseError(url=url)
        
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
        s.settimeout(10)  # Optional: wait up to 5 seconds

        try:
            # region - initialize connection
            print("initializing")
            packet = struct.pack("!qii", PROTOCOL_ID, 0, TRANSACTION_ID) # ACTION: connect
            s.sendto(packet, (HOSTNAME, PORT))
            response, addr = s.recvfrom(1024)  # buffer size can be adjusted
            # You can unpack the response here depending on expected format
            CONNECTION_ID = initializing_validator(response)
            # endregion

            # region - query
            print("querying")
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
            raise TQError.TimeoutError(url=url)
        except socket.error as e:
            raise TQError.UnexpectedError(url=url, e=e)
        finally:
            s.close()
        
        return udp_response_parser(response)

def query(url: str,
            info_hash: str,
            peer_id: str,  
            event: int, 
            left = 0, downloaded = 0, uploaded = 0, 
            ip_addr:str = "0.0.0.0",
            num_want = -1, key = random.randint(0, 0xFFFF),
            port:int = 6881, headers = None ) -> bool:
        
    if url.startswith("http"):
        return Query.http(url,
                          info_hash,
                          peer_id,
                          event,
                          left, downloaded, uploaded,
                          port, headers)
    elif url.startswith("udp"):
        if event == "none":
            event = 0
        elif event == "completed":
            event = 1
        elif event == "started":
            event = 2
        elif event == "stopped":
            event = 3

        return Query.udp(url,
                         info_hash,
                         peer_id,
                         2,
                         left, downloaded, uploaded,
                         ip_addr, num_want, key,
                         port)
    else:
        raise TQError.TrackerQueryException(message="Unsupported URL scheme", url=url)