from pidng.core import RPICAM2DNG, DNGTags, Tag
from pidng.camdefs import *
import numpy as np
import matplotlib.pyplot as plt

# load raw image data from file into numpy array. RAW frame from HQ camera. 
img = '../rpicam-raw-20-6-2024--15.12.3\BGGRss1200gain0.1---00001.raw'
# "C:\Users\matth\code\PiDNG\rpicam-raw-20-6-2024--15.12.3\BGGRss1200gain0.1---00001.dng"
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
# camera = RaspberryPiHqCamera(3, CFAPattern.BGGR)
# [0, 0, 0, 0] is equal to a RRRR monochrome filter
# in order for this to work, we need to rewrite the blue and green pixels
camera = RaspberryPiHqCamera(3, [2, 1, 1, 0])

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

def redShiftFilter(rawFrame):
    height, width = rawFrame.shape
    for x in range(0, width): # width
        for y in range(0, height): # height
            if(y % 2 == 0):
                if(x % 2 == 0): # blue
                    # get nearest red
                    targetRedX =  x + 1
                    targetRedY = y + 1
                else: # green
                    targetRedX =  x
                    targetRedY = y + 1
            else:
                if(x % 2 == 0): # green
                    targetRedX =  x + 1
                    targetRedY = y
                else: # red
                    targetRedX =  x
                    targetRedY = y
            rawFrame[y][x] = rawFrame[targetRedY][targetRedX]
    return rawFrame

def medianRedShiftFilter(rawFrame):
    height, width = rawFrame.shape
    for col in range(1, width): # width
        for row in range(1, height): # height
            if(row % 2 == 0):
                if(col % 2 == 0): # blue
                    # get nearest red
                    reds = [rawFrame[row - 1][col - 1], rawFrame[row - 1][col + 1], rawFrame[row + 1][col - 1], rawFrame[row + 1][col + 1]]
                else: # green
                    reds = [rawFrame[row - 1][col], rawFrame[row + 1][col]]
            else:
                if(col % 2 == 0): # green
                    reds = [rawFrame[row][col - 1], rawFrame[row][col + 1]]
                else: # red
                    reds = [rawFrame[row][col]]
            average = int(sum(reds) / len(reds))
            rawFrame[row][col] = average
    return rawFrame

def smartMedianRedShiftFilter(rawFrame):
    height, width = rawFrame.shape
    for col in range(1, width): # width
        for row in range(1, height): # height
            if(row % 2 == 0):
                if(col % 2 == 0): # blue
                    # get nearest red
                    reds = [rawFrame[row - 1][col - 1], rawFrame[row - 1][col + 1], rawFrame[row + 1][col - 1], rawFrame[row + 1][col + 1]]
                else: # green
                    reds = [abs(rawFrame[row][col] - 200) * 4]
            else:
                if(col % 2 == 0): # green
                    reds = [abs(rawFrame[row][col] - 200) * 4]
                else: # red
                    reds = [rawFrame[row][col]]
            average = int(sum(reds) / len(reds))
            rawFrame[row][col] = average
    return rawFrame


globalBlueArray = 0
globalGreenArray = 0
globalRedArray = 0
def getColorArrays(rawFrame):
    height, width = rawFrame.shape

    blueArray = np.zeros((int(height / 2), int(width / 2)), dtype=np.uint16)
    blueArray[:, :] = rawFrame[::2, ::2]
    print(blueArray[1000,1000])

    redArray = np.zeros((int(height / 2), int(width / 2)), dtype=np.uint16)
    redArray[:, :] = rawFrame[1::2, 1::2]
    print(redArray[1000,1000])

    greenArray = np.zeros((int(height), int(width / 2)), dtype=np.uint16)
    # get even rows (BG rows)
    greenArray[::2, :] = rawFrame[::2, 1::2]
    # get odd rows (GR rows)
    greenArray[1::2, :] = rawFrame[1::2, ::2]

    global globalBlueArray
    globalBlueArray = blueArray

    global globalRedArray
    globalRedArray = redArray

    global globalGreenArray
    globalGreenArray = greenArray

    return rawFrame

def normalizeBluePixels(rawFrame):
    height, width = rawFrame.shape
    for col in range(1, width): # width
        for row in range(1, height): # height
            if(row % 2 == 0):
                if(col % 2 == 0): # blue
                    # get nearest red
                    nearValues = [rawFrame[row - 1][col - 1], rawFrame[row - 1][col + 1], rawFrame[row + 1][col - 1], rawFrame[row + 1][col + 1]]
                    average = int(sum(nearValues) / len(nearValues))
                    rawFrame[row][col] = average
    return rawFrame

def normalizePixels(rawFrame):
    # lowest possible value for the sensor https://www.strollswithmydog.com/pi-hq-cam-sensor-performance/
    IMX477_BLACK_LEVEL = 255
    GREEN_PIXEL_MULTIPLIER = 3.5
    BLUE_PIXEL_MULTIPLIER = 10
    height, width = rawFrame.shape
    newFrame = np.zeros((height, width), dtype=np.uint16)

    red_data = rawFrame[1::2, 1::2]
    green_data_even_rows = rawFrame[::2, 1::2]
    green_data_odd_rows = rawFrame[1::2, ::2]
    blue_data = rawFrame[::2, ::2]

    red_conditional = red_data > 1100
    green_even_row_conditional = green_data_even_rows < 400
    green_odd_row_conditional = green_data_odd_rows < 400
    blue_conditional = blue_data < 300

    normalized_green_on_even_rows = (abs(green_data_even_rows - IMX477_BLACK_LEVEL) * GREEN_PIXEL_MULTIPLIER) + IMX477_BLACK_LEVEL
    normalized_green_on_odd_rows = (abs(green_data_odd_rows - IMX477_BLACK_LEVEL) * GREEN_PIXEL_MULTIPLIER) + IMX477_BLACK_LEVEL
    normalized_blue_data = (abs(blue_data - IMX477_BLACK_LEVEL) * BLUE_PIXEL_MULTIPLIER) + IMX477_BLACK_LEVEL

    modified_red_data = np.where(red_conditional, IMX477_BLACK_LEVEL, red_data)
    modified_green_even_row_data = np.where(green_even_row_conditional, IMX477_BLACK_LEVEL, normalized_green_on_even_rows)
    modified_green_odd_row_data = np.where(green_odd_row_conditional, IMX477_BLACK_LEVEL, normalized_green_on_odd_rows)
    modified_blue_data = np.where(blue_conditional, IMX477_BLACK_LEVEL, blue_data)

    # Setting these as integers and not floating point numbers is important. The resulting image will be broken.
    # I believe it is due to floating point numbers as binary cannot be packed as expected
    # blue
    # newFrame[::2, ::2] = normalized_blue_data
    newFrame[::2, ::2] = blue_data

    # green even
    # newFrame[::2, 1::2] = np.floor(normalized_green_on_even_rows).astype(int)
    newFrame[::2, 1::2] = green_data_even_rows

    # green odd
    # newFrame[1::2, ::2] = np.floor(normalized_green_on_odd_rows).astype(int)
    newFrame[1::2, ::2] = green_data_odd_rows

    # red
    newFrame[1::2, 1::2] = modified_red_data

    return newFrame

# pass camera reference into the converter.
r = RPICAM2DNG(camera)
r.options(path="C:/Users/matth/code/PiDNG/rpicam-raw-20-6-2024--13.0.24", compress=False)
r.filter = normalizePixels
r.convert(data, filename="./red-modx-1-red-bean")

# blueDataToPlot = np.ascontiguousarray(globalBlueArray).view(np.uint16)
# plt.figure(figsize=(12, 8))
# print(str(globalRedArray[1000,1000]))
# plt.boxplot(globalRedArray)
# plt.show()

# B G B G B G
# G R G R G R
# B G B G B G
# G R G R G R
# B G B G B G
# G R G R G R

# 283 / 314 = .9
# 40 / 
