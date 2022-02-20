from pidng.core import RPICAM2DNG, DNGTags, Tag
from pidng.camdefs import *
import numpy as np

img = "frame_000032.raw"
data = np.fromfile(img, dtype=np.uint8)

camera = RaspberryPiHqCamera(1, CFAPattern.BGGR)

r = RPICAM2DNG(camera)
r.options(path="", compress=True)
r.convert(data, filename="custom2")
