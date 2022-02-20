from pidng.core import RPICAM2DNG, DNGTags, Tag
from pidng.camdefs import *
import numpy as np


data = np.ndarray((4056,3040))

camera = RaspberryPiHqCamera(3, CFAPattern.BGGR)

r = RPICAM2DNG(camera)
r.options(path="")
r.convert(data, filename="custom")
