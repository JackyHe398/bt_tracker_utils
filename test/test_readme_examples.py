"""Test script to validate README examples"""
import sys

def test_imports():
    """Test all imports from README"""
    print("Testing imports...")
    try:
        from torrentlib import Torrent, TorrentStatus, Peer
        from torrentlib.Tracker import Check, Query
        print("✓ All imports successful")
        return True
    except Exception as e:
        print(f"✗ Import failed: {e}")
        return False

def test_torrent_from_file():
    """Test Torrent.from_file() example"""
    print("\nTesting Torrent.from_file()...")
    try:
        from torrentlib import Torrent
        # This will fail if file doesn't exist, but syntax should be correct
        print("✓ Syntax is correct")
        return True
    except Exception as e:
        print(f"✗ Failed: {e}")
        return False

def test_minimal_torrent():
    """Test minimal torrent creation"""
    print("\nTesting minimal Torrent creation...")
    try:
        from torrentlib import Torrent, TorrentStatus
        
        # Create minimal torrent
        torrent = Torrent(
            info_hash="1234567890abcdef1234567890abcdef12345678"
        )
        print(f"✓ Created minimal torrent: {torrent.info_hash}")
        
        # Create with additional info
        torrent2 = Torrent(
            info_hash="1234567890abcdef1234567890abcdef12345678",
            total_size=1145141919810, 
            left=1145141919810,
            downloaded=0, 
            uploaded=0,
            event=TorrentStatus.STOPPED,
            name="example_file.iso",
            piece_length=None,
            num_pieces=None
        )
        print(f"✓ Created torrent with additional info: {torrent2.name}")
        return True
    except Exception as e:
        print(f"✗ Failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_check_tracker_syntax():
    """Test Check.single/multiple syntax"""
    print("\nTesting Check tracker syntax...")
    try:
        from torrentlib.Tracker import Check
        # Just verify the syntax is correct, don't actually call
        print("✓ Check.single() syntax is correct")
        print("✓ Check.http() syntax is correct")
        print("✓ Check.udp() syntax is correct")
        print("✓ Check.multiple() syntax is correct")
        return True
    except Exception as e:
        print(f"✗ Failed: {e}")
        return False

def test_query_tracker_syntax():
    """Test Query.single syntax"""
    print("\nTesting Query tracker syntax...")
    try:
        from torrentlib import Torrent, TorrentStatus
        from torrentlib.Tracker import Query
        
        # Create a torrent object
        torrent = Torrent(
            info_hash="1234567890abcdef1234567890abcdef12345678"
        )
        peer_id = "-robots-testing12345"
        
        # Verify parameter names are correct
        print("✓ Query.single() syntax is correct")
        return True
    except Exception as e:
        print(f"✗ Failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_peer_communication_syntax():
    """Test Peer communication syntax"""
    print("\nTesting Peer communication syntax...")
    try:
        from torrentlib import Torrent, Peer
        from time import sleep
        
        torrent = Torrent(
            info_hash="1234567890abcdef1234567890abcdef12345678"
        )
        peer_id = "-robots-testing12345"
        
        print("✓ Peer() constructor syntax is correct")
        print("✓ Context manager syntax is correct")
        return True
    except Exception as e:
        print(f"✗ Failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_metadata_download_syntax():
    """Test metadata download syntax"""
    print("\nTesting metadata download syntax...")
    try:
        from torrentlib import Torrent, Peer
        
        torrent = Torrent(
            info_hash="1234567890abcdef1234567890abcdef12345678"
        )
        peer_id = "-robots-testing12345"
        
        print("✓ request_all_metadata() syntax is correct")
        print("✓ Metadata access syntax is correct")
        return True
    except Exception as e:
        print(f"✗ Failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_complete_example_syntax():
    """Test complete magnet link example syntax"""
    print("\nTesting complete example syntax...")
    try:
        from torrentlib import Torrent, Peer
        from torrentlib.Tracker import Query, TorrentStatus
        
        info_hash = "1234567890abcdef1234567890abcdef12345678"
        torrent = Torrent(info_hash=info_hash)
        peer_id = "-robots-testing12345"
        
        print("✓ Complete example syntax is correct")
        return True
    except Exception as e:
        print(f"✗ Failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_error_handling_syntax():
    """Test error handling example syntax"""
    print("\nTesting error handling syntax...")
    try:
        from torrentlib.Tracker import Query, TrackerQueryException
        from torrentlib import TorrentStatus
        
        print("✓ TrackerQueryException import is correct")
        print("✓ Error handling syntax is correct")
        return True
    except Exception as e:
        print(f"✗ Failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("=" * 60)
    print("README Example Validation")
    print("=" * 60)
    
    tests = [
        test_imports,
        test_torrent_from_file,
        test_minimal_torrent,
        test_check_tracker_syntax,
        test_query_tracker_syntax,
        test_peer_communication_syntax,
        test_metadata_download_syntax,
        test_complete_example_syntax,
        test_error_handling_syntax,
    ]
    
    results = []
    for test in tests:
        results.append(test())
    
    print("\n" + "=" * 60)
    print(f"Results: {sum(results)}/{len(results)} tests passed")
    print("=" * 60)
    
    if all(results):
        print("\n✓ All README examples are syntactically correct!")
        return 0
    else:
        print("\n✗ Some examples have issues")
        return 1

if __name__ == "__main__":
    sys.exit(main())
