import requests
import struct
import random
import socket
from bencodepy import decode as bdecode, exceptions as bexceptions
from urllib.parse import urlparse
from collections.abc import Iterable


class CheckTracker:
    @staticmethod
    def http(url: str, timeout: int = 5) -> bool:
        """
        Check if a given HTTP URL is reachable and returns a status code.
        """
        info_hash_hex = '8a19577fb5f690970ca43a57ff1011ae202244b8'
        info_hash_bytes = bytes.fromhex(info_hash_hex)

        headers = {
            "User-Agent": "qBittorrent/4.5.2",  # Mimic a known client
            "Accept": "*/*",
            "Connection": "close"
        }

        params = {
            'info_hash': info_hash_bytes,
            'peer_id': '-robots-testing12345',
            'left': '0',
            'port': '6881',
            'downloaded': '0',
            'uploaded': '0',
            'event': 'stopped',
        }

        try:
            response = requests.get(url,
                                    headers=headers,
                                    params=params,
                                    allow_redirects=True,
                                    timeout=timeout)
        except requests.exceptions.Timeout as e:
            print(f"❌ {url}: Timeout - {e}")
            return False
        except requests.exceptions.RequestException as e:
            print(f"❌ {url}: Unexpected error - {e}")
            return False
        
        sc = response.status_code
        if sc == 200:
            print(f"✅ {url}: Active")
            try: 
                bdecode(response.content)
                return True
            except bexceptions.DecodingError as e:
                print(f"❌ {url}: Invalid response format - {e}")
                return False
        elif sc == 400: 
            print(f"⚠️ {url}: Active, (400) Bad Request")
            return False
        else:
            print(f"⚠️ Responded but not valid: {url} ({response.status_code})")
            return False

    @staticmethod
    def udp(url: str, timeout: int = 5) -> bool:
        def response_validator(response, id)-> bool:
            action, transaction_id, connection_id = struct.unpack("!iiq", response[:16])
            if action == ACTION and transaction_id == id:
                print(f"✅ {url}: Active")
                return True
            else:
                print(f"❌ {url}: Invalid response")
                return False
            
        parsed = urlparse(url)
        HOSTNAME = parsed.hostname
        PORT = parsed.port

        # Constants
        PROTOCOL_ID = 0x41727101980    # 8-byte magic number
        ACTION = 0                     # Connect = 0
        id = random.randint(0, 0xFFFF)  # Random 4-byte integer

        # Create packet: ! means network byte order (big-endian)
        packet = struct.pack("!qii", PROTOCOL_ID, ACTION, id)

        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(timeout)  # Optional: wait up to 5 seconds

        try:
            s.sendto(packet, (HOSTNAME, PORT))
            response, addr = s.recvfrom(1024)  # buffer size can be adjusted
            # You can unpack the response here depending on expected format
            return response_validator(response, id)
        except socket.timeout:
            print(f"❌ {url}: Request timed out")
            return False
        finally:
            s.close()

def check_trackers(urls: Iterable, max_threads=50, timeout: int = 5):
    import threading
    semaphore = threading.Semaphore(max_threads)
    def threaded_check(url):
        with semaphore:
            result = check_tracker(url)
            results[url] = result

    results = {}
    threads = []

    for url in urls:
        t = threading.Thread(target=threaded_check, args=(url,))
        t.start()
        threads.append(t)

    for t in threads:
        t.join()


    # Final list of active trackers
    print("\n\n\n🧲 Active Trackers List:")
    for url, status in results.items():
        if status:
            print(url)

def check_tracker(url: str, timeout: int = 5) -> bool:
    if url.startswith("http"):
        return CheckTracker.http(url, timeout=timeout)
    elif url.startswith("udp"):
        return CheckTracker.udp(url, timeout=timeout)
    else:
        print(f"❌ Unsupported scheme: {url}")
        return False