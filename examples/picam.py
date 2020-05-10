import time
import picamera
from io import BytesIO
import numpy as np
from pydng.core import RPICAM2DNG

# using RPICAM2DNG with a stream output such as what is given in picamera. Examples assumes use of OV5647. 

with picamera.PiCamera(sensor_mode=2) as camera:

    stream = BytesIO()

    camera.resolution = (2592,1944)
    camera.iso = 100
    time.sleep(2)

    camera.framerate = 5
    
    camera.start_preview()
    camera.shutter_speed = camera.exposure_speed
    camera.exposure_mode = 'off'
    g = camera.awb_gains
    camera.awb_mode = 'off'
    camera.awb_gains = g

    time.sleep(10)
    camera.capture(stream, 'jpeg', bayer=True)
    start_time = time.time()
    d = RPICAM2DNG()
    output = d.convert(stream)
    print("--- %s seconds ---" % (time.time() - start_time))
    with open('image.dng', 'wb') as f:
            f.write(output)
    time.sleep(10)

    camera.stop_preview()