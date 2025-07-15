import requests
import struct
import random
import socket
from urllib.parse import urlparse


class check_tracker:
    def http(url: str) -> bool:
        """
        Check if a given HTTP URL is reachable and returns a status code.
        """
        headers = {
            "User-Agent": "qBittorrent/4.5.2",  # Mimic a known client
            "Accept": "*/*",
            "Connection": "close"
            }
        try:
            response = requests.get(url, headers=headers, timeout=5)
            sc = response.status_code
            if sc == 200 or sc == 400 or sc == 406:
                print(f"✅ {url}: Active")
                return True
            else:
                print(f"⚠️ Responded but not valid: {url} ({response.status_code})")
        except requests.exceptions.RequestException as e:
            print(f"❌ Error: {url} - {e}")
        return False

    def udp(url: str) -> bool:
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
        s.settimeout(5)  # Optional: wait up to 5 seconds

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
