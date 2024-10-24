import subprocess
from pathlib import Path
from threading import Thread
import datetime
import os
import cmd
from flask import Flask

from pidng.core import RPICAM2DNG, DNGTags, Tag
from pidng.camdefs import *
import numpy as np

class BayerFilterValue:
    B = 2
    G = 1
    R = 0

class RpiCam():
    DEFAULT_WRITE_LOCATION = '/media/matthewverde/RAW/'
    def __init__(self, shutterSpeed, analogGain, framerate, recordingTime):
        self.shutterSpeed = shutterSpeed
        self.analogGain = analogGain
        self.framerate = framerate
        self.recordingTime = recordingTime
        self.outputLocation = self.DEFAULT_WRITE_LOCATION
        self.setRawFilePrefix()
        self.cameraName = 'imx477'
        self.bit = '12'
        self.format = 'SRGGB12_CSI2P'
        self.setBayerFilter('BGGR')
        self.setMode(3)
        self.quickFilter = 't'
        self.convertToDng = 't'

    def getParentDirectoryForRecording(self):
        now = datetime.datetime.now()
        newDirName = f'rpicam-raw-{now.day}-{now.month}-{now.year}--{now.hour}.{now.minute}.{now.second}'
        newDirLocation = os.path.join(self.outputLocation, newDirName)
        os.mkdir(newDirLocation)
        return newDirLocation

    def getRpiCamOutputFilePath(self, parentPath):
        return os.path.join(parentPath, f'{self.bayerFilterString}{self.rawFilePrefix}%05d.raw')

    def setBayerFilter(self, colorPattern):
        pattern = []
        for color in colorPattern:
            if color == 'B' or color == 'b':
                pattern.append(BayerFilterValue.B)
            elif color == 'G' or color == 'g':
                pattern.append(BayerFilterValue.G)
            elif color == 'R' or color == 'r':
                pattern.append(BayerFilterValue.R)
        self.bayerFilter = pattern
        self.bayerFilterString = colorPattern
    
    def setShutterSpeed(self, value):
        self.shutterSpeed = value
        self.setRawFilePrefix()

    def setGain(self, value):
        self.analogGain = value
        self.setRawFilePrefix()

    def setRawFilePrefix(self):
        self.rawFilePrefix = f'ss{self.shutterSpeed}gain{self.analogGain}---'
    
    def setMode(self, modeToSet):
        if(modeToSet == 1):
            self.mode = 1
            self.width = '2028'
            self.height = '1080'
            self.stride = '3072'
        elif(modeToSet == 2):
            self.mode = 2
            self.width = '2028'
            self.height = '1520'
            self.stride = '3072'
        elif(modeToSet == 3):
            self.mode = 3
            self.width = '4056'
            self.height = '3040'
            self.stride = '6112'
        else:
            print(f'mode but be the value 1, 2, or 3. Got: {modeToSet}')

    def printConfig(self):
        configString = f'''
            *** Cam Config ***\n
            camera name: {self.cameraName}\n
            bayer filter: {self.bayerFilterString}\n
            shutter speed: {self.shutterSpeed}\n
            analog gain: {self.analogGain}\n
            frame rate: {self.framerate}\n
            recording time: {self.recordingTime}\n
            size: {self.width}x{self.height}\n
            mode: {self.mode}\n
            bit: {self.bit}
        '''
        print(configString)
        return configString

    def record(self):
        parentDir = self.getParentDirectoryForRecording()
        rawOutputFilePath = self.getRpiCamOutputFilePath(parentDir)
        processArguments = ['rpicam-raw', '-t', self.recordingTime, '--segment', '1', '-o', rawOutputFilePath, '--framerate', self.framerate, '--gain', self.analogGain, '--shutter', self.shutterSpeed, '--width', self.width, '--height', self.height]
        print('*** Starting Recording ***')
        print(f'cmd: {" ".join(processArguments)}')
        process = subprocess.run(processArguments, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print('*** Recording Finshed ***')
        if(self.convertToDng == 't'):
            print('*** Converting raw files to dng ***')
            dngConverter = PiDngManager(self)
            dngConverter.convert(parentDir, True)



class CommandHandler(cmd.Cmd):
    prompt = ">>> "

    def __init__(self, cam):
        super().__init__()
        self.cam = cam

    def do_framerate(self, arg):
        self.cam.framerate = arg

    def do_gain(self, arg):
        self.cam.setGain(arg)

    def do_rec_time(self, arg):
        self.cam.recordingTime = arg

    def do_shutter_speed(self, arg):
        self.cam.setShutterSpeed(arg)

    def do_config(self, arg):
        self.cam.printConfig()

    def do_rec(self, arg):
        self.cam.record()

    def do_mode(self, arg):
        self.cam.setMode(int(arg))

    def do_filter(self, arg):
        self.cam.setBayerFilter(arg)

    def do_quick_filter(self, arg):
        self.cam.quickFilter = arg

    def do_convert(self, arg):
        self.cam.convertToDng = arg

    def do_exit(self, arg):
        return True

MICROSECONDS_PER_SECOND = 1000000

class PiDngManager():
    def __init__(self, cam):
        self.cam = cam

    def convert(self, dirToConvert, convertAll):
        camera = RaspberryPiHqCamera(self.cam.mode, self.cam.bayerFilter)
        # camera.tags.set(Tag.ApertureValue, [[4,1]])             # F 4.0
        # camera.tags.set(Tag.PhotographicSensitivity, [1000])     # ISO 400
        exposureTimeDenominator = int(int(self.cam.shutterSpeed) / MICROSECONDS_PER_SECOND)
        camera.tags.set(Tag.ExposureTime, [[1,exposureTimeDenominator]])
        camera.fmt = dict({
            # tuple is in the form width height
            'size': (int(self.cam.width), int(self.cam.height)),
            'bpp': int(self.cam.bit),
            'format': self.cam.format
        })
        # pass camera reference into the converter.
        r = RPICAM2DNG(camera)
        r.options(path=dirToConvert, compress=False)
        if(self.cam.bayerFilter == [BayerFilterValue.R, BayerFilterValue.R, BayerFilterValue.R, BayerFilterValue.R]):
            if(self.cam.quickFilter != 't'):
                # slow as shit
                r.filter = self.medianRedShiftFilter
            else:
                r.filter = self.redShiftFilter
        else:
            r.filter = self.noOpFilter
        print(f'Converting raw files in {dirToConvert} to DNG')
        for dirpath, dirnames, filenames in os.walk(dirToConvert):
            if(convertAll):
                for filename in filenames:
                    print(f'Converting: {filename} to DNG')
                    fileNameDng = Path(filename).with_suffix(".dng")
                    data = np.fromfile(os.path.join(dirToConvert, filename), dtype=np.uint8)
                    data = data.reshape((int(self.cam.height), int(self.cam.stride)))
                    r.convert(data, filename=os.path.join(dirToConvert, fileNameDng))

    def noOpFilter(self, rawFrame):
        return rawFrame

    def redShiftFilter(self, rawFrame):
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

    # slow as shit
    def medianRedShiftFilter(self, rawFrame):
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

# app = Flask(__name__)
# globalCam = RpiCam('100000', '1.0', '10', '1000')
# @app.route('/api/config/')
# def get_config():
#     return globalCam.printConfig()

# @app.route('/')
# def get_wow():
#     print('wow')
#     return 'hello'

def main():
    # shutterSpeed (microseconds), analogGain, framerate, recordingTime
    cam = RpiCam('1200', '0.5', '10', '1000')
    # app.run(debug=True, host='0.0.0.0', port=8080)
    commandHandler = CommandHandler(cam)
    commandHandler.cmdloop()

main()
