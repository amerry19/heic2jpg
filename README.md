# heic2jpg
Python library that watches filesystem and automatically converts HEIC images as they appear into JPG files. No more manual file conversions!

## Dependencies
ImageMagick: ```brew install imagemagick```

## How to run
From the project root: ``` python3 heic2jpg.py ~/ ```

## TODO:

* Add CLI args
  * Persist options
* Args
  * Preferred dir to watch
  * Auto-trash incoming HEIC images once conversion is complete
* Run in background and not in shell