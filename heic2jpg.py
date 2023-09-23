#!/usr/bin/env python3

import os
import time
import subprocess
import argparse
import configparser
import send2trash
import logging
import glob
from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler


def get_config():
    config = configparser.ConfigParser()
    config.read("heic2jpg.ini")

    # Load previous settings or defaults
    dir = config.get("Settings", "dir", fallback=os.path.expanduser("~"))
    autodelete = config.getboolean("Settings", "autodelete", fallback=False)
    immediate = config.getboolean("Settings", "immediate", fallback=False)

    return config, dir, autodelete, immediate


def update_config(config, directory="~", autodelete=False, immediate=False):
    # Save settings
    config["Settings"] = {
        "dir": directory,
        "autodelete": str(autodelete),
        "immediate": str(immediate)
    }
    with open("heic2jpg.ini", "w") as configfile:
        config.write(configfile)


def parse_arguments():
    # Def command-line arguments
    parser = argparse.ArgumentParser(description="Converts HEIC files to JPG")
    parser.add_argument("-dir", help="Directory to watch for changes")
    parser.add_argument("-i", "--immediate", action="store", choices=["true", "false"],
                        help="Convert the existing HEIC files in the directory before starting the watcher")
    parser.add_argument("-autodelete", action="store", choices=["true", "false"],
                        help="Automatically delete HEIC file after successful conversion")
    parser.add_argument("-reset", action="store_true", help="Reset to default settings")

    # Parse command-line arguments
    args = parser.parse_args()

    return args


def reset_config(config):
    # Reset configurations to defaults
    update_config(config)


class ImageConverter:
    def __init__(self, directory, logger, autodelete=False):
        """
        Initialize an ImageConverter instance.

        :param directory: The directory containing HEIC files.
        :type directory: str
        :param logger: The logger object for logging messages.
        :type logger: logging.Logger
        :param autodelete: Whether to automatically delete HEIC files after conversion. Defaults to False.
        :type autodelete: bool, optional
        """
        self.directory = directory
        self.logger = logger
        self.autodelete = autodelete

    def convert_existing(self):
        """
        Converts existing HEIC files in the directory to JPG
        """
        self.logger.info(f"Converting existing HEIC files in {self.directory} to JPG...")
        for file in glob.iglob(f"{self.directory}/**/*.[hH][eE][iI][cC]", recursive=True):
            self.heic_to_jpg(file)

    def heic_to_jpg(self, path):
        """
        Convert a HEIC file to JPG.

        :param path: The path to the HEIC file to convert.
        :type path: str
        """
        self.logger.info(f"Converting {path} to jpg...")
        conversion = subprocess.run(["magick", "convert", path, f"{os.path.splitext(path)[0]}.jpg"])
        self.logger.info(f"Conversion finished for {path}")

        if self.autodelete and conversion.returncode == 0:
            self.delete_file(path)

    def delete_file(self, path):
        """
        Send a file to the trash.

        :param path: The path to the file to delete.
        :type path: str
        """
        max_retries = 10
        delay = 0.5  # delay in seconds
        for i in range(max_retries):
            try:
                time.sleep(delay)  # wait a bit before deleting
                self.logger.info(f"Deleting original HEIC file: {path}")
                send2trash.send2trash(path)
                break  # if deletion was successful, break out of the loop
            except Exception as e:
                if i < max_retries - 1:  # if this wasn't the last attempt
                    self.logger.warning(
                        f"Error deleting file {path}, retrying in {delay} seconds. Error was {e}")
                    time.sleep(delay)  # wait a bit before retrying
                else:
                    self.logger.error(f"Error deleting file {path}, giving up. Error was {e}")


class FileHandler(PatternMatchingEventHandler):
    patterns = ["*.heic", "*.jpg"]

    def __init__(self, image_converter, logger, *args, **kwargs):
        super(FileHandler, self).__init__(*args, **kwargs)
        self.image_converter = image_converter
        self.logger = logger

    def process(self, event):
        self.logger.info(f"{event.src_path} has been {event.event_type}")

        # If the file is in the trash, ignore the event
        if ".Trash" in event.src_path.split(os.sep):
            self.logger.info(f"Ignoring event in trash: {event.src_path}")
            return

        if event.event_type == "created" and event.src_path.lower().endswith(".heic"):
            self.image_converter.heic_to_jpg(event.src_path)

    def on_modified(self, event):
        self.process(event)

    def on_created(self, event):
        self.process(event)


def setup_logger(log_file=None):
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)  # Or DEBUG, ERROR, etc.

    # Create formatter
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

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
    config, directory, autodelete, immediate = get_config()

    # If -reset flag is provided, reset the configuration and exit
    if args.reset:
        reset_config(config)
        print("Configuration has been reset. Exiting the script.")
        return

    # If -dir argument is specified, update setting
    if args.dir:
        directory = args.dir

    # If -autodelete argument is given, update setting
    if args.autodelete is not None:
        autodelete = args.autodelete.lower() == "true"

    # If -immediate argument is given, update setting
    if args.immediate is not None:
        immediate = args.immediate.lower() == "true"

    # Update configurations
    update_config(config, directory, autodelete, immediate)

    logger = setup_logger(log_file="heic2jpg.log")
    path = os.path.abspath(directory)

    image_converter = ImageConverter(path, logger, autodelete=autodelete)
    if immediate:
        image_converter.convert_existing()

    logger.info(f"Watching directory: {path}")
    observer = Observer()
    handler = FileHandler(image_converter, logger=logger)
    observer.schedule(handler, directory, recursive=True)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()

    observer.join()


if __name__ == "__main__":
    main()
