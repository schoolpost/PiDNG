from pidng import RAW2DNG, DNGTags, Tag
import numpy as np
import struct

# image specs
width = 4096
height = 3072
bpp= 12

# load raw data into 16-bit numpy array.
numPixels = width*height
rawFile = 'extras/scene_daylight_211ms_c2.raw16'
rf = open(rawFile, mode='rb')
rawData = struct.unpack("H"*numPixels,rf.read(2*numPixels))
rawFlatImage = np.zeros(numPixels, dtype=np.uint16)
rawFlatImage[:] = rawData[:] 
rawImage = np.reshape(rawFlatImage,(height,width))
rawImage = rawImage >> (16 - bpp)

# uncalibrated color matrix, just for demo. 
ccm1 = [[19549, 10000], [-7877, 10000], [-2582, 10000],	
        [-5724, 10000], [10121, 10000], [1917, 10000],
        [-1267, 10000], [ -110, 10000], [ 6621, 10000]]

# set DNG tags.
t = DNGTags()
t.set(Tag.ImageWidth, width)
t.set(Tag.ImageLength, height)
t.set(Tag.TileWidth, width)
t.set(Tag.TileLength, height)
t.set(Tag.Orientation, 1)
t.set(Tag.PhotometricInterpretation, 32803)
t.set(Tag.SamplesPerPixel, 1)
t.set(Tag.BitsPerSample, bpp)
t.set(Tag.CFARepeatPatternDim, [2,2])
t.set(Tag.CFAPattern, [1, 2, 0, 1])
t.set(Tag.BlackLevel, (4096 >> (16 - bpp)))
t.set(Tag.WhiteLevel, ((1 << bpp) -1) )
t.set(Tag.ColorMatrix1, ccm1)
t.set(Tag.CalibrationIlluminant1, 21)
t.set(Tag.AsShotNeutral, [[1,1],[1,1],[1,1]])
t.set(Tag.DNGVersion, [1, 4, 0, 0])
t.set(Tag.DNGBackwardVersion, [1, 2, 0, 0])
t.set(Tag.Make, "Camera Brand")
t.set(Tag.Model, "Camera Model")
t.set(Tag.PreviewColorSpace, 2)

# save to dng file.
RAW2DNG().convert(rawImage, tags=t, filename="custom", path="")