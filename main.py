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
        try:
            response = requests.get(tracker, headers=headers, timeout=5)
            sc = response.status_code
            if sc == 200 or sc == 400 or sc == 406:
                print(f"✅ Active: {tracker}")
                return True
            else:
                print(f"⚠️ Responded but not 200: {tracker} ({response.status_code})")
        except requests.exceptions.RequestException as e:
            print(f"❌ Error: {tracker} - {e}")
        return False

    def udp(url: str) -> bool:
        parsed = urlparse(url)
        HOSTNAME = parsed.hostname
        PORT = parsed.port
        PATH = parsed.path

        # Constants
        PROTOCOL_ID = 0x41727101980    # 8-byte magic number
        ACTION = 0                     # Connect = 0
        id = random.randint(0, 0xFFFFFFFF)  # Random 4-byte integer

        # Create packet: ! means network byte order (big-endian)
        packet = struct.pack("!qii", PROTOCOL_ID, ACTION, id)

        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.sendto(packet, (HOSTNAME, PORT))  # Send to tracker on port 80

# Set of tracker URLs to check
old = set()
with open("trackers.txt", "r") as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith("#"):  # Ignore empty lines and comments
            old.add(line)
# List to store confirmed active trackers
trackers = []
headers = {
    "User-Agent": "qBittorrent/4.5.2",  # Mimic a known client
    "Accept": "*/*",
    "Connection": "close"
}

# Loop through and test each tracker
for tracker in old:
    # protocol parser
    if tracker.startswith("http://"):
        appends = check_tracker.http(tracker)
    elif tracker.startswith("udp://"):
        appends = check_tracker.http(tracker)

# Final list of active trackers
print("\n🧲 Active Trackers List:")
for t in trackers:
    print(t)