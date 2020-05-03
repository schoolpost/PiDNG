#!/usr/bin/python3.7

import sys
import struct
import os, io
import time
import array
import getopt
import platform
import operator
import errno
import numpy as np
from ljpegCompress import pack16tolj
import exifread
import ctypes

from .dng import Type, Tag, dngHeader, dngIFD, dngTag, DNG

class BroadcomRawHeader(ctypes.Structure):
    _fields_ = [
        ('name',          ctypes.c_char * 32),
        ('width',         ctypes.c_uint16),
        ('height',        ctypes.c_uint16),
        ('padding_right', ctypes.c_uint16),
        ('padding_down',  ctypes.c_uint16),
        ('dummy',         ctypes.c_uint32 * 6),
        ('transform',     ctypes.c_uint16),
        ('format',        ctypes.c_uint16),
        ('bayer_order',   ctypes.c_uint8),
        ('bayer_format',  ctypes.c_uint8),
    ]

BAYER_ORDER = {
    0: [0, 1, 1, 2],
    1: [1, 2, 0, 1],
    2: [2, 1, 1, 0],
    3: [1, 0, 2, 1],
}

CAMERA_VERSION = {
    "RP_ov5647": "Raspberry Pi Camera V1",
    "RP_imx219": "Raspberry Pi Camera V2",
}


def parseTag(s):
    s = str(s)
    try:
        return [[int(s.split('/')[0]), int(s.split('/')[1])]]
    except:
        return [[int(s), 1]]


def pack10(data):
    out = np.zeros((data.shape[0], int(data.shape[1]*(1.25))), dtype=np.uint8)
    out[:,::5] = data[:,::4] >> 2
    out[:,1::5] = ((data[:,::4] & 0b0000000000000011 ) << 6)
    out[:,1::5] += data[:,1::4] >> 4
    out[:,2::5] = ((data[:,1::4] & 0b0000000000001111 ) << 4)
    out[:,2::5] += data[:,2::4] >> 6
    out[:,3::5] = ((data[:,2::4] & 0b0000000000111111 ) << 2)
    out[:,3::5] += data[:,3::4] >> 8
    out[:,4::5] = data[:,3::4] & 0b0000000011111111 
    return out


def pack12(data):
    out = np.zeros((data.shape[0], int(data.shape[1]*(1.5)) ), dtype=np.uint8)
    out[:,::3] = data[:,::2] >> 4
    out[:,1::3] = ((data[:,::2] & 0b0000000000001111 ) << 4)
    out[:,1::3] += data[:,1::2] >> 8
    out[:,2::3] = data[:,1::2] & 0b0000001111111111 
    return out

class DNGConverter:
    def __init__(self, dark=None, shade=None):
        self.dark = dark
        self.shade = shade
        self.header = None
        self.__exif__ = None
        self.etags = {
                    'EXIF DateTimeDigitized':None, 
                    'EXIF FocalLength':None, 
                    'EXIF ExposureTime':None, 
                    'EXIF ISOSpeedRatings':None, 
                    'EXIF ApertureValue':None, 
                    'EXIF ShutterSpeedValue':None, 
                    'Image Model':None, 
                    'Image Make':None, 
                    'EXIF WhiteBalance':None 
                    }
    
    def __extractRAW__(self, img):
        file = open(img, 'rb')

        self.__exif__ = exifread.process_file(file)
        stream = io.BytesIO(file.read())

        ver = {
        'RP_ov5647': 1,
        'RP_imx219': 2,
        }[str(self.__exif__['Image Model'])]

        offset = {
            1: 6404096,
            2: 10270208,
        }[ver]


        data = stream.getvalue()[-offset:]

        self.header = BroadcomRawHeader.from_buffer_copy(data[176:176 + ctypes.sizeof(BroadcomRawHeader)])

        data = data[32768:]
        data = np.frombuffer(data, dtype=np.uint8)

        reshape, crop = {
            1: ((1952, 3264), (1944, 3240)),
            2: ((2480, 4128), (2464, 4100)),
        }[ver]
        data = data.reshape(reshape)[:crop[0], :crop[1]]

        data = data.astype(np.uint16) << 2
        for byte in range(4):
            data[:, byte::5] |= ((data[:, 4::5] >> ((byte+1) * 2)) & 0b11)
        data = np.delete(data, np.s_[4::5], 1)

        return data
    
    def __process__(self, input_file, processing=False):

        # extract bayer raw to 16bit numpy array
        rawImage = self.__extractRAW__(input_file)

        if processing:

            if self.shade:
                shading = self.__extractRAW__(self.shade)
                
            if self.dark:
                dark = self.__extractRAW__(self.dark)


            rawImage[1::2, 0::2] = (rawImage[1::2, 0::2]) - np.mean(dark[1::2, 0::2])
            rawImage[0::2, 0::2] = (rawImage[0::2, 0::2]) - np.mean(dark[0::2, 0::2])
            rawImage[1::2, 1::2] = (rawImage[1::2, 1::2]) - np.mean(dark[1::2, 1::2])
            rawImage[0::2, 1::2] = (rawImage[0::2, 1::2]) - np.mean(dark[0::2, 1::2])

            shading[1::2, 0::2] = shading[1::2, 0::2] - np.mean(dark[1::2, 0::2])
            shading[0::2, 0::2] = shading[0::2, 0::2] - np.mean(dark[0::2, 0::2])
            shading[1::2, 1::2] = shading[1::2, 1::2] - np.mean(dark[1::2, 1::2])
            shading[0::2, 1::2] = shading[0::2, 1::2] - np.mean(dark[0::2, 1::2])

            rawImage = rawImage.astype(np.uint16)
            shading = shading.astype(np.uint16)

            temp = np.zeros(rawImage.shape, dtype=np.uint16)
            temp[1::2, 0::2] = rawImage[1::2, 0::2] * ( np.mean(shading[1::2, 0::2]) / shading[1::2, 0::2] ) #RED
            temp[0::2, 0::2] = rawImage[0::2, 0::2] * ( np.mean(shading[0::2, 0::2]) / shading[0::2, 0::2] ) #GREEN
            temp[1::2, 1::2] = rawImage[1::2, 1::2] * ( np.mean(shading[1::2, 1::2]) / shading[1::2, 1::2] ) #GREEN
            temp[0::2, 1::2] = rawImage[0::2, 1::2] * ( np.mean(shading[0::2, 1::2]) / shading[0::2, 1::2] ) #BLUE

            rawImage = temp.astype(np.uint16)

            raw_r = rawImage[1::2, 0::2]
            raw_b = rawImage[0::2, 1::2]
            raw_g = ((rawImage[0::2, 0::2] + rawImage[1::2, 1::2])/2).astype(np.uint16)

            # [1::2, 0::2] #RED
            # [0::2, 0::2] #GREEN 
            # [1::2, 1::2] #GREEN
            # [0::2, 1::2] #BLUE

            r_pm = np.amax(raw_r).astype(np.uint16)
            b_pm = np.amax(raw_b).astype(np.uint16)
            g_pm = np.amax(raw_g).astype(np.uint16)

            pm = np.array([r_pm, g_pm, b_pm])

            if np.amin(pm) < 1023:
                rawImage = np.clip(rawImage, 0, np.amin(pm))
            else:
                rawImage = np.clip(rawImage, 0, 1023)

            rawImage = rawImage.astype(np.uint16)

        return rawImage

    
    def convert(self, inputFilename, width=None, length=None, process=False):
        dngTemplate = DNG()

        rawFrame = self.__process__(inputFilename)
        for k,v in self.etags.items():
            self.etags[k] = self.__exif__[k]
        
        if not width:
            width = int(str(self.__exif__['Image ImageWidth']))
        if not length:
            length  = int(str(self.__exif__['Image ImageLength']))

        tile = pack16tolj(rawFrame,int(width*2),int(length/2),10,0,0,0,"",2)
        dngTemplate.ImageDataStrips.append(tile)

        print(len(tile))

        cfa_pattern = BAYER_ORDER[self.header.bayer_order]
        camera_version  = CAMERA_VERSION[str(self.etags['Image Model'])]
        
        # set up the FULL IFD
        mainIFD = dngIFD()
        mainTagStripOffset = dngTag(Tag.TileOffsets, [0 for tile in dngTemplate.ImageDataStrips])
        mainIFD.tags.append(mainTagStripOffset)
        mainIFD.tags.append(dngTag(Tag.NewSubfileType           , [0]))
        mainIFD.tags.append(dngTag(Tag.TileByteCounts          , [len(tile) for tile in dngTemplate.ImageDataStrips]))
        mainIFD.tags.append(dngTag(Tag.ImageWidth               , [width]))
        mainIFD.tags.append(dngTag(Tag.ImageLength              , [length]))
        mainIFD.tags.append(dngTag(Tag.SamplesPerPixel          , [1]))
        mainIFD.tags.append(dngTag(Tag.BitsPerSample            , [10]))
        mainIFD.tags.append(dngTag(Tag.TileWidth             , [width]))
        mainIFD.tags.append(dngTag(Tag.TileLength             , [length]))
        mainIFD.tags.append(dngTag(Tag.Compression              , [7])) 
        mainIFD.tags.append(dngTag(Tag.PhotometricInterpretation, [32803])) 
        mainIFD.tags.append(dngTag(Tag.CFARepeatPatternDim      , [2, 2]))
        mainIFD.tags.append(dngTag(Tag.CFAPattern               , cfa_pattern))
        mainIFD.tags.append(dngTag(Tag.BlackLevel               , [np.amin(rawFrame)]))
        mainIFD.tags.append(dngTag(Tag.WhiteLevel               , [np.amax(rawFrame)]))
        mainIFD.tags.append(dngTag(Tag.Make                     , str(self.etags['Image Make'])))
        mainIFD.tags.append(dngTag(Tag.Model                    , str(self.etags['Image Model'])))
        mainIFD.tags.append(dngTag(Tag.ApertureValue            , parseTag(self.etags['EXIF ApertureValue'])))
        mainIFD.tags.append(dngTag(Tag.ShutterSpeedValue        , parseTag(self.etags['EXIF ShutterSpeedValue'])))
        mainIFD.tags.append(dngTag(Tag.FocalLength              , parseTag(self.etags['EXIF FocalLength'])))
        mainIFD.tags.append(dngTag(Tag.ExposureTime             , parseTag(self.etags['EXIF ExposureTime'])))
        mainIFD.tags.append(dngTag(Tag.DateTime                 , str(self.etags['EXIF DateTimeDigitized'])))
        mainIFD.tags.append(dngTag(Tag.PhotographicSensitivity  , [int(str(self.etags['EXIF ISOSpeedRatings']))] ))
        mainIFD.tags.append(dngTag(Tag.Software                 , "PyDNG"))
        mainIFD.tags.append(dngTag(Tag.Orientation              , [1]))
        mainIFD.tags.append(dngTag(Tag.DNGVersion               , [1, 4, 0, 0]))
        mainIFD.tags.append(dngTag(Tag.DNGBackwardVersion       , [1, 2, 0, 0]))
        mainIFD.tags.append(dngTag(Tag.UniqueCameraModel        , camera_version))
        mainIFD.tags.append(dngTag(Tag.ColorMatrix1             , [[19549, 10000], [-7877, 10000], [-2582, 10000],	
                                                                [-5724, 10000], [10121, 10000], [1917, 10000],
                                                                [-1267, 10000], [ -110, 10000], [ 6621, 10000]]))
        mainIFD.tags.append(dngTag(Tag.ColorMatrix2             , [[13244, 10000], [-5501, 10000], [-1248, 10000],	
                                                                [-1508, 10000], [9858, 10000], [1935, 10000],
                                                                [-270, 10000], [ -1083, 10000], [ 4366, 10000]]))
        mainIFD.tags.append(dngTag(Tag.AsShotNeutral            , [[10043,10000],[16090,10000],[10000,10000]]))
        mainIFD.tags.append(dngTag(Tag.NoiseProfile   , [0.000393625,0.000000122976 ]))
        mainIFD.tags.append(dngTag(Tag.CalibrationIlluminant1   , [1]))
        mainIFD.tags.append(dngTag(Tag.CalibrationIlluminant2   , [23]))
        mainIFD.tags.append(dngTag(Tag.PreviewColorSpace   , [2]))

        dngTemplate.IFDs.append(mainIFD)

        totalLength = dngTemplate.dataLen()

        mainTagStripOffset.setValue([k for offset,k in dngTemplate.StripOffsets.items()])

        buf = bytearray(totalLength)
        dngTemplate.setBuffer(buf)
        dngTemplate.write()

        outputDNG = inputFilename.strip('.jpg') + '.dng'

        outfile = open(outputDNG, "wb")
        outfile.write(buf)
        outfile.close()
    

        
        
