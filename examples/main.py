import subprocess
from threading import Thread
import datetime
import os

DEFAULT_WRITE_LOCATION = '/media/matthewverde/RAW/'

def record():
    recordingTime = '1000'
    framerate = '15'
    gain = '5.0'
    filename = 'image'

    now = datetime.datetime.now()
    newDirName = f'rpicam-raw-{now.day}-{now.month}-{now.year}--{now.hour}.{now.minute}.{now.second}'
    newDirLocation = os.path.join(DEFAULT_WRITE_LOCATION, newDirName)
    os.mkdir(newDirLocation)
    outputLocation = os.path.join(newDirLocation, f'{filename}%05d.raw')

    process = subprocess.run(['rpicam-raw', '-t', recordingTime, '--segment', '1', '-o', outputLocation, '--framerate', framerate, '--gain', gain], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    print(process)

record()