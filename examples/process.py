from pydng.core import RPICAM2DNG
import numpy as np

def processing(raw):
    # access to the bayer raw numpy array here. 
    print(raw.shape, raw.size)
    return raw

RPICAM2DNG().convert("imx477.jpg", process=processing)