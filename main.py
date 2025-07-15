from check_tracker import check_tracker

# Set of tracker URLs to check
old = set()
with open("trackers.txt", "r") as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith("#"):  # Ignore empty lines and comments
            old.add(line)
# List to store confirmed active trackers
trackers = []

# Loop through and test each tracker
for tracker in old:
    # protocol parser
    if tracker.startswith("http://"):
        appends = check_tracker.http(tracker)
    elif tracker.startswith("udp://"):
        appends = check_tracker.udp(tracker)

# Final list of active trackers
print("\n🧲 Active Trackers List:")
for t in trackers:
    print(t)