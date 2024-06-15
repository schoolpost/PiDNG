import subprocess
from threading import Thread
import datetime
import os

def record() {
    recordingTime = '1000'
    framerate = '15'
    gain = '5.0'
    filename = 'image'

    now = datetime.datetime.now()
    os.mkdir(now)
    cwd = os.getcwd()
    outputLocation = os.path.join(cwd, f'{now}/{filename}%05d.raw')

    process = subprocess.Popen(['rpicam-raw', f'-t {recordingTime}', '--segment 1', f'-o {outputLocation}', f'--framerate {framerate}', f'--gain {gain}'], stdout=subprocess.PIPE, stderr=subprocess.PIPE
}