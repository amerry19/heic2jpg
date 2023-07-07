#!/usr/bin/env python3

import os
import sys
import time
import subprocess
from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler

class FileHandler(PatternMatchingEventHandler):
    patterns = ["*.heic", "*.jpg"]

    def process(self, event):
        print(f"{event.src_path} has been {event.event_type}")
        if event.event_type == 'created' or event.event_type == 'modified':
            # If a .heic file has been created or modified, convert it to .jpg
            if event.src_path.lower().endswith(".heic"):
                print(f"Converting {event.src_path} to jpg...")
                subprocess.run(['magick', 'convert', event.src_path, f'{os.path.splitext(event.src_path)[0]}.jpg'])
                print(f"Conversion finished for {event.src_path}")

    def on_modified(self, event):
        self.process(event)

    def on_created(self, event):
        self.process(event)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Please provide a directory to watch as a command line argument.")
        sys.exit(1)

    path = sys.argv[1]  
    print(f"Script started. Watching directory: {os.path.abspath(path)}")

    observer = Observer()
    observer.schedule(FileHandler(), path, recursive=True)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()

    observer.join()
