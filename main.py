from bt_tracker_utils import CheckTracker, check_trackers
if __name__ == "__main__":
    # Set of tracker URLs to check
    urls = set()
    with open("trackers.txt", "r") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):  # Ignore empty lines and comments
                urls.add(line)

    check_trackers(urls)