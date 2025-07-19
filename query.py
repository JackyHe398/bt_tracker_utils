import requests
import struct
import random
import socket
import bencode as bec
from typing import Dict, Any
from urllib.parse import urlparse
import TrackerQueryException as TQError


class query:
    def http(url: str) -> Dict[str, Any]:
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
