# heic2jpg
Python library that watches filesystem and automatically converts HEIC images as they appear into JPG files. No more manual file conversions!

## Dependencies
ImageMagick: ```brew install imagemagick```

## How to run
From the project root: ```python3 heic2jpg.py```

## Command-line Arguments

heic2jpg supports the following command-line arguments:

- `-dir`: Specifies the directory to watch for changes. By default, the script watches the user's home directory.
- `-autodelete`: Enables automatic deletion (moves to trash [OS agnostic]) of HEIC files after successful conversion. By default, auto-deletion is disabled.
- `-reset`: Resets the configuration to default settings, using the user's home directory and disabling auto-deletion.

To use these command-line arguments, run the script with the desired options. Here are some examples:

```bash
# Watch a specific directory and enable auto-deletion
python3 heic2jpg.py -dir /path/to/directory -autodelete

# Reset the configuration to default settings
python3 heic2jpg.py -reset
