from picamera2.picamera2 import *
import time

picam2 = Picamera2()
picam2.start_preview()

preview_config = picam2.preview_configuration(raw={"size": picam2.sensor_resolution})
picam2.configure(preview_config)

settings = {"ExposureTime": 16667, "AnalogueGain": 1.0}

picam2.start(settings)
picam2.options = {"compress_level": 1}

picam2.capture_file("output")
picam2.stop()

