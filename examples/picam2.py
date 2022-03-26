from null_preview import *
from picamera2 import *
import time

picam2 = Picamera2()
preview = NullPreview(picam2)

preview_config = picam2.preview_configuration(raw={"size": picam2.sensor_resolution})
picam2.configure(preview_config)

settings = {"ExposureTime": 16667, "AnalogueGain": 4.0}

picam2.start(settings)
picam2.options = {"compress_level": 1}

picam2.capture_file("output")
print(picam2.stream_configuration("raw"))
print(picam2.camera_configuration())

picam2.stop()

