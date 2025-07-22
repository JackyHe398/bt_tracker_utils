from check_tracker import check_tracker
from collections.abc import Iterable
import threading

def check_trackers(urls: Iterable, max_threads=50):
    semaphore = threading.Semaphore(max_threads)
    def threaded_check(url):
        with semaphore:
            if url.startswith("http"):
                result = check_tracker.http(url)
            elif url.startswith("udp"):
                result = check_tracker.udp(url)
            else:
                print(f"❌ Unsupported scheme: {url}")
                result = False
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

if __name__ == "__main__":
    # Set of tracker URLs to check
    urls = set()
    with open("trackers.txt", "r") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):  # Ignore empty lines and comments
                urls.add(line)

    check_trackers(urls)