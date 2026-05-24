from pidng.core import RPICAM2DNG, DNGTags, Tag
from pidng.camdefs import *
import numpy as np

# load raw image data from file into numpy array. RAW frame from HQ camera. 
img = '../raw-test-full-sensor/test00000.raw'
data = np.fromfile(img, dtype=np.uint8)
# file size 4669440
# (1520 height) * (((2028 width * 12 bits per pixel) / 8 bits per byte) + 30 extra bytes*) = 4669440 bytes
# (((2028 * 12) / 8) + 30) = 3072
# bytes*: strolls with dog claims it should only by 28 extra bytes https://www.strollswithmydog.com/open-raspberry-pi-high-quality-camera-raw/
# tuple is in the form row, col
# data = data.reshape((1520, 3072))
data = data.reshape((3040, 6112))

# choose a predefined camera model, set the sensor mode and bayer layout. 
# this camera model class sets the appropriate DNG's tags needed based on the camera sensor. ( needed for bit unpacking, color matrices )
camera = RaspberryPiHqCamera(3, CFAPattern.BGGR)

# if self.mode == 1:
#     width = 2028
#     height = 1080
# if self.mode == 2:
#     width = 2028
#     height = 1520
# if self.mode == 3:
#     width = 4056
#     height = 3040
# if self.mode == 4:
#     width = 1012
#     height = 760

# example of adding custom DNG tags to predefined tags from camera model
camera.tags.set(Tag.ApertureValue, [[4,1]])             # F 4.0
camera.tags.set(Tag.ExposureTime, [[1,300]])             # SHUTTER 1/400
camera.tags.set(Tag.PhotographicSensitivity, [1000])     # ISO 400
camera.fmt = dict({
    # tuple is in the form width height
    'size': (4056,3040),
    'bpp': 12,
    'format': 'SRGGB12_CSI2P'
})

# pass camera reference into the converter.
r = RPICAM2DNG(camera)
r.options(path="C:/Users/matth/code/PiDNG/raw-test-full-sensor", compress=False)
r.convert(data, filename="./full-sensor-test")
