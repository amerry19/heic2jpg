#!/usr/bin/env python3

import os
import time
import subprocess
import argparse
import configparser
import send2trash
import logging
from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler


def get_config():
    config = configparser.ConfigParser()
    config.read('heic2jpg.ini')

    # Load previous settings or defaults
    dir = config.get('Settings', 'dir', fallback=os.path.expanduser("~"))
    autodelete = config.getboolean('Settings', 'autodelete', fallback=False)

    return config, dir, autodelete


def update_config(config, dir, autodelete):
    # Save settings
    config['Settings'] = {'dir': dir, 'autodelete': str(autodelete)}
    with open('heic2jpg.ini', 'w') as configfile:
        config.write(configfile)


def parse_arguments():
    # Def command-line arguments
    parser = argparse.ArgumentParser(description="Converts HEIC files to JPG")
    parser.add_argument("-dir", help="Directory to watch for changes")
    parser.add_argument("-autodelete", action='store', choices=['true', 'false'], help="Automatically delete HEIC file after successful conversion")
    parser.add_argument("-reset", action='store_true', help="Reset to default settings")

    # Parse command-line arguments
    args = parser.parse_args()

    return args
def reset_config(config):
    # Reset settings to defaults
    dir = os.path.expanduser("~")
    autodelete = False

    # Update configurations
    update_config(config, dir, autodelete)

class FileHandler(PatternMatchingEventHandler):
    patterns = ["*.heic", "*.jpg"]

    def __init__(self, autodelete, logger, *args, **kwargs):
        super(FileHandler, self).__init__(*args, **kwargs)
        self.autodelete = autodelete
        self.logger = logger

    def process(self, event):
        self.logger.info(f"{event.src_path} has been {event.event_type}")

        # If the file is in the trash, ignore the event
        if ".Trash" in event.src_path.split(os.sep):
            self.logger.info(f"Ignoring event in trash: {event.src_path}")
            return

        if event.event_type == 'created' and event.src_path.lower().endswith(".heic"):
            self.convert_heic_to_jpg(event)

    def convert_heic_to_jpg(self, event):
        # If a .heic file has been created or modified, convert it to .jpg
        self.logger.info(f"Converting {event.src_path} to jpg...")
        conversion = subprocess.run(['magick', 'convert', event.src_path, f'{os.path.splitext(event.src_path)[0]}.jpg'])
        self.logger.info(f"Conversion finished for {event.src_path}")

        if self.autodelete and conversion.returncode == 0:
            self.delete_file(event)

    def delete_file(self, event):
        MAX_RETRIES = 10
        DELAY = 0.5  # delay in seconds
        for i in range(MAX_RETRIES):
            try:
                time.sleep(DELAY)  # wait a bit before deleting
                self.logger.info(f"Deleting original HEIC file: {event.src_path}")
                send2trash.send2trash(event.src_path)
                break  # if deletion was successful, break out of the loop
            except Exception as e:
                if i < MAX_RETRIES - 1:  # if this wasn't the last attempt
                    self.logger.warning(f"Error deleting file {event.src_path}, retrying in {DELAY} seconds. Error was {e}")
                    time.sleep(DELAY)  # wait a bit before retrying
                else:
                    self.logger.error(f"Error deleting file {event.src_path}, giving up. Error was {e}")

    def on_modified(self, event):
        self.process(event)

    def on_created(self, event):
        self.process(event)


def setup_logger(log_file=None):
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)  # Or DEBUG, ERROR, etc.

    # Create formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # Create console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # Create file handler if log_file is provided
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


def main():
    args = parse_arguments()

    # Load configurations
    config, dir, autodelete = get_config()

    # If -reset flag is provided, reset the configuration and exit
    if args.reset:
        reset_config(config)
        print("Configuration has been reset. Exiting the script.")
        return

    # If -dir argument is specified, update setting
    if args.dir:
        dir = args.dir

    # If -autodelete argument is given, update setting
    if args.autodelete is not None:
        autodelete = args.autodelete.lower() == 'true'

    # Update configurations
    update_config(config, dir, autodelete)

    logger = setup_logger(log_file='heic2jpg.log')

    logger.info(f"Script started. Watching directory: {os.path.abspath(dir)}")

    observer = Observer()
    observer.schedule(FileHandler(autodelete=autodelete, logger=logger), dir, recursive=True)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()

    observer.join()


if __name__ == "__main__":
    main()
