from pidng.core import RPICAM2DNG, DNGTags, Tag
from pidng.camdefs import *
import numpy as np
import tkinter
from tkinter import *

def getRGBHex(value, color):
    hexVal =  hex(value)[2:]

    if(len(hexVal) == 0):
        hexVal = '000'
    if(len(hexVal) == 1):
        hexVal = f'00{hexVal}'
    if(len(hexVal) == 2):
        hexVal = f'0{hexVal}'
        
    if(color == 'r'):
        return f'#{hexVal}000000'
    if(color == 'g'):
        return f'#000{hexVal}000'
    if(color == 'b'):
        return f'#000000{hexVal}'

master = Tk()
w = Canvas(master, width=1700, height=800)
w.pack()
canvas_height=3040
canvas_width=4056
y = int(canvas_height / 2)
for i in range(0, 100):
    w.create_line(0, i, 200, i, fill=getRGBHex(900, 'g'))

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
# for i in range(6112 - 50, 6112):
#     print("{:08b}".format(data[1][i]))

for i in range(0, 12):
    print("{:08b}".format(data[0][i]))

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

# 4095
# example of passing a filter over the rawframe before it is saved. This will simply print the dimensions of the raw image. 
def print_dimensions(rawFrame):
    height, width = rawFrame.shape
    for x in range(0, 1700): # width
        for y in range(0, 800): # height
            if(y % 2 == 0):
                if(x % 2 == 0): # blue
                    w.create_line(x, y, x+1, y, fill=getRGBHex(rawFrame[y][x], 'b'))
                else: # green
                    w.create_line(x, y, x+1, y, fill=getRGBHex(rawFrame[y][x], 'g'))
            else:
                if(x % 2 == 0): # green
                    w.create_line(x, y, x+1, y, fill=getRGBHex(rawFrame[y][x], 'g'))
                else: # red
                    w.create_line(x, y, x+1, y, fill=getRGBHex(rawFrame[y][x], 'r'))

    print(f'width: {width}')
    print(f'height {height}')
    # print(rawFrame[0,0])
    return rawFrame

# pass camera reference into the converter.
r = RPICAM2DNG(camera)
r.options(path="C:/Users/matth/code/PiDNG/raw-test-full-sensor", compress=False)
r.filter = print_dimensions
r.convert(data, filename="./full-sensor-test")
unpackedPixel = r.__unpack_pixels__(data=data)
# print('first pixel')
# print(unpackedPixel[0,0])
# print('second pixel')
# print(unpackedPixel[0,1])
# print('third pixel')
# print(unpackedPixel[0,2])
mainloop()
