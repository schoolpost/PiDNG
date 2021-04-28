#!/usr/bin/python3.7

import sys
import struct
import os
import io
import time
import array
import getopt
import platform
import operator
import errno
import types
import numpy as np
import exifread
import ctypes
import zlib

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
    "RP_testc": "Raspberry Pi High Quality Camera",
    "RP_imx477": "Raspberry Pi High Quality Camera",
    "imx477": "Raspberry Pi High Quality Camera",
}

SENSOR_NATIVE_BPP = {
    "RP_ov5647": 10,
    "RP_imx219": 10,
    "RP_testc": 12,
    "RP_imx477": 12,
    "imx477": 12
}


def parseTag(s):
    s = str(s)
    try:
        return [[int(s.split('/')[0]), int(s.split('/')[1])]]
    except:
        return [[int(s), 1]]


def pack10(data):
    out = np.zeros((data.shape[0], int(data.shape[1]*(1.25))), dtype=np.uint8)
    out[:, ::5] = data[:, ::4] >> 2
    out[:, 1::5] = ((data[:, ::4] & 0b0000000000000011) << 6)
    out[:, 1::5] += data[:, 1::4] >> 4
    out[:, 2::5] = ((data[:, 1::4] & 0b0000000000001111) << 4)
    out[:, 2::5] += data[:, 2::4] >> 6
    out[:, 3::5] = ((data[:, 2::4] & 0b0000000000111111) << 2)
    out[:, 3::5] += data[:, 3::4] >> 8
    out[:, 4::5] = data[:, 3::4] & 0b0000000011111111
    return out


def pack12(data):
    out = np.zeros((data.shape[0], int(data.shape[1]*(1.5))), dtype=np.uint8)
    out[:, ::3] = data[:, ::2] >> 4
    out[:, 1::3] = ((data[:, ::2] & 0b0000000000001111) << 4)
    out[:, 1::3] += data[:, 1::2] >> 8
    out[:, 2::3] = data[:, 1::2] & 0b0000001111111111
    return out

# todo


def pack14(data):
    out = np.zeros((data.shape[0], int(data.shape[1]*(1.75))), dtype=np.uint8)
    out[:, ::7] = data[:, ::6] >> 6
    out[:, 1::7] = ((data[:, ::6] & 0b0000000000000011) << 6)
    out[:, 1::7] += data[:, 1::6] >> 8
    out[:, 2::7] = ((data[:, 1::6] & 0b0000000000001111) << 4)
    out[:, 2::7] += data[:, 2::6] >> 6
    out[:, 3::7] = ((data[:, 2::6] & 0b0000000000111111) << 2)
    out[:, 3::7] += data[:, 3::6] >> 8
    out[:, 4::7] = ((data[:, 3::6] & 0b0000000000001111) << 4)
    out[:, 4::7] += data[:, 4::6] >> 6
    out[:, 5::7] = ((data[:, 4::6] & 0b0000000000111111) << 2)
    out[:, 5::7] += data[:, 5::6] >> 8
    out[:, 6::7] = data[:, 5::6] & 0b0000000011111111
    pass


def blockshaped(arr, nrows, ncols):
    """
    Return an array of shape (n, nrows, ncols) where
    n * nrows * ncols = arr.size
    If arr is a 2D array, the returned array should look like n subblocks with
    each subblock preserving the "physical" layout of arr.
    """
    h, w = arr.shape
    return (arr.reshape(h//nrows, nrows, -1, ncols)
               .swapaxes(1, 2)
               .reshape(-1, nrows, ncols))


def parseMaker(s):
    d = dict()
    d['unk'] = list()
    for param in s.split(" "):
        if "=" in param:
            d[param.split("=")[0]] = param.split("=")[1]
        else:
            d["unk"].append(param)
    return d


class RPICAM2DNG:
    def __init__(self):
        self.header = None
        self.__exif__ = None
        self.maker_note = None
        self.etags = {
            'EXIF DateTimeDigitized': None,
            'EXIF FocalLength': 0,
            'EXIF ExposureTime': 0,
            'EXIF ISOSpeedRatings': 0,
            'EXIF ApertureValue': 0,
            'EXIF ShutterSpeedValue': 0,
            'Image Model': "",
            'Image Make': "",
            'EXIF WhiteBalance': 0,
            'Image ImageWidth': 0,
            'Image ImageLength': 0
        }

    def __extractRAW__(self, img):

        isfile = False

        if isinstance(img, str) and os.path.exists(img):
            isfile = True
        elif isinstance(img, io.BytesIO):
            isfile = False
        else:
            raise ValueError
        if isfile:
            file = open(img, 'rb')
            img = io.BytesIO(file.read())
            self.__exif__ = exifread.process_file(img)
        else:
            img.seek(0)
            self.__exif__ = exifread.process_file(img)

        ver = {
            'RP_ov5647': 1,
            'RP_imx219': 2,
            'RP_testc': 3,
            'RP_imx477': 3,
            "imx477": 3,
        }[str(self.__exif__['Image Model'])]

        if int(str(self.__exif__['Image ImageWidth'])) == 2028 \
            and int(str(self.__exif__['Image ImageLength'])) == 1520 \
                and ver == 3:
            ver = 4

        offset = {
            1: 6404096,
            2: 10270208,
            3: 18711040,
            4: 4751360,
        }[ver]

        self.maker_note = parseMaker(
            bytearray(self.__exif__['EXIF MakerNote'].values).decode())

        data = img.getvalue()[-offset:]
        assert data[:4] == 'BRCM'.encode("ascii")

        self.header = BroadcomRawHeader.from_buffer_copy(
            data[176:176 + ctypes.sizeof(BroadcomRawHeader)])

        data = data[32768:]
        data = np.frombuffer(data, dtype=np.uint8)

        reshape, crop = {
            1: ((1952, 3264), (1944, 3240)),
            2: ((2480, 4128), (2464, 4100)),
            3: ((3056, 6112), (3040, 6084)),
            4: ((1536, 3072), (1520, 3042)),
        }[ver]
        data = data.reshape(reshape)[:crop[0], :crop[1]]

        if ver < 3:
            data = data.astype(np.uint16) << 2
            for byte in range(4):
                data[:, byte::5] |= (
                    (data[:, 4::5] >> ((4 - byte) * 2)) & 0b11)
            data = np.delete(data, np.s_[4::5], 1)
        else:
            data = data.astype(np.uint16)
            shape = data.shape
            unpacked_data = np.zeros(
                (shape[0], int(shape[1] / 3 * 2)), dtype=np.uint16)
            unpacked_data[:, ::2] = (data[:, ::3] << 4) + \
                (data[:, 2::3] & 0x0F)
            unpacked_data[:, 1::2] = (
                data[:, 1::3] << 4) + ((data[:, 2::3] >> 4) & 0x0F)
            data = unpacked_data

        return data

    def __process__(self, input_file, processing):

        rawImage = self.__extractRAW__(input_file)

        if not processing:
            return rawImage

        elif isinstance(processing, types.FunctionType):

            if isinstance(input_file, str):
                processed = processing(rawImage, input_file)
            else:
                processed = processing(rawImage)
            if not isinstance(processed, np.ndarray):
                raise TypeError("return value is not a valid numpy array!")
            elif processed.shape != rawImage.shape:
                raise ValueError("return array does not have the same shape!")
            if processed.dtype != np.uint16:
                raise ValueError("array data type is invalid!")

            return processed

        else:
            raise TypeError("process arguement is not a valid function!")

    def convert(self, image, width=None, length=None, process=None, compress=False, bpp=None):
        dngTemplate = DNG()

        file_output = False

        if isinstance(image, str):
            file_output = True
        elif isinstance(image, io.BytesIO):
            file_output = False
        else:
            raise ValueError

        rawFrame = self.__process__(image, process)
        for k, v in self.etags.items():
            try:
                self.etags[k] = self.__exif__[k]
            except KeyError:
                self.etags[k] = 0

        if not width:
            width = int(self.header.width)

        if not length:
            length = int(self.header.height)

        cfa_pattern = BAYER_ORDER[self.header.bayer_order]
        camera_version = CAMERA_VERSION[str(self.etags['Image Model'])]

        sensor_bpp = SENSOR_NATIVE_BPP[str(self.etags['Image Model'])]
        if not bpp:
            bpp = sensor_bpp

        sensor_black = 4096 >> (16 - bpp)
        sensor_white = (1 << bpp) - 1

        profile_name = "Standard Profile"
        profile_embed = 3
        fm = False

        rphq_str = ('RP_testc', 'imx477', 'RP_imx477')

        if str(self.etags['Image Model']) in rphq_str:

            profile_name = "Repro 2_5D no LUT - D65 is really 5960K"

            ccm1 = [[6759, 10000], [-2379, 10000], [751, 10000],
                    [-4432, 10000], [13871, 10000], [5465, 10000],
                    [-401, 10000], [1664, 10000], [7845, 10000]]

            ccm2 = [[5603, 10000], [-1351, 10000], [-600, 10000],
                    [-2872, 10000], [11180, 10000], [2132, 10000],
                    [600, 10000], [453, 10000], [5821, 10000]]

            fm = True

            fm1 = [[7889, 10000], [1273, 10000], [482, 10000],
                   [2401, 10000], [9705, 10000], [-2106, 10000],
                   [-26, 10000], [-4406, 10000], [12683, 10000]]

            fm2 = [[6591, 10000], [3034, 10000], [18, 10000],
                   [1991, 10000], [10585, 10000], [-2575, 10000],
                   [-493, 10000], [-919, 10000], [9663, 10000]]

            ci1 = 17
            ci2 = 21

        else:
            as_shot_neutral = [[10043, 10000], [16090, 10000], [10000, 10000]]

            ccm1 = [[19549, 10000], [-7877, 10000], [-2582, 10000],
                    [-5724, 10000], [10121, 10000], [1917, 10000],
                    [-1267, 10000], [-110, 10000], [6621, 10000]]

            ccm2 = [[13244, 10000], [-5501, 10000], [-1248, 10000],
                    [-1508, 10000], [9858, 10000], [1935, 10000],
                    [-270, 10000], [-1083, 10000], [4366, 10000]]
            ci1 = 1
            ci2 = 23

        baseline_exp = 1
        
        camera_calibration = [[1, 1], [0, 1], [0, 1],
                              [0, 1], [1, 1], [0, 1],
                              [0, 1], [0, 1], [1, 1]]

        if self.maker_note:
            gain_r = int(float(self.maker_note['gain_r'])*1000)
            gain_b = int(float(self.maker_note['gain_b'])*1000)

            baseline_exp = int(self.maker_note['ev'])

            as_shot_neutral = [[1000, gain_r], [1000, 1000], [1000, gain_b]]

        compression_scheme = 7 if compress else 1

        if compress:
            from ljpegCompress import pack16tolj
            tile = pack16tolj(rawFrame, int(width*2),
                              int(length/2), bpp, 0, 0, 0, "", 6)
        else:
            if (bpp - sensor_bpp) >= 0:
                rawFrame = rawFrame << (bpp - sensor_bpp)
            else:
                rawFrame = rawFrame >> abs(bpp - sensor_bpp)

            if bpp == 8:
                tile = (rawFrame//255).astype('uint8').tobytes()
            elif bpp == 10:
                tile = pack10(rawFrame).tobytes()
            elif bpp == 12:
                tile = pack12(rawFrame).tobytes()
            elif bpp == 14:
                tile = pack14(rawFrame).tobytes()
            elif bpp == 16:
                tile = rawFrame.tobytes()

        dngTemplate.ImageDataStrips.append(tile)
        # set up the FULL IFD
        mainIFD = dngIFD()
        mainTagStripOffset = dngTag(
            Tag.TileOffsets, [0 for tile in dngTemplate.ImageDataStrips])
        mainIFD.tags.append(mainTagStripOffset)
        mainIFD.tags.append(dngTag(Tag.NewSubfileType, [0]))
        mainIFD.tags.append(dngTag(Tag.TileByteCounts, [len(
            tile) for tile in dngTemplate.ImageDataStrips]))
        mainIFD.tags.append(dngTag(Tag.ImageWidth, [width]))
        mainIFD.tags.append(dngTag(Tag.ImageLength, [length]))
        mainIFD.tags.append(dngTag(Tag.SamplesPerPixel, [1]))
        mainIFD.tags.append(dngTag(Tag.BitsPerSample, [bpp]))
        mainIFD.tags.append(dngTag(Tag.TileWidth, [width]))
        mainIFD.tags.append(dngTag(Tag.TileLength, [length]))
        mainIFD.tags.append(dngTag(Tag.Compression, [compression_scheme]))
        mainIFD.tags.append(dngTag(Tag.PhotometricInterpretation, [32803]))
        mainIFD.tags.append(dngTag(Tag.CFARepeatPatternDim, [2, 2]))
        mainIFD.tags.append(dngTag(Tag.CFAPattern, cfa_pattern))
        mainIFD.tags.append(dngTag(Tag.BlackLevel, [sensor_black]))
        mainIFD.tags.append(dngTag(Tag.WhiteLevel, [sensor_white]))
        mainIFD.tags.append(dngTag(Tag.Make, str(self.etags['Image Make'])))
        mainIFD.tags.append(dngTag(Tag.Model, str(self.etags['Image Model'])))
        mainIFD.tags.append(
            dngTag(Tag.ApertureValue, parseTag(self.etags['EXIF ApertureValue'])))
        mainIFD.tags.append(dngTag(Tag.ShutterSpeedValue, parseTag(
            self.etags['EXIF ShutterSpeedValue'])))
        mainIFD.tags.append(
            dngTag(Tag.FocalLength, parseTag(self.etags['EXIF FocalLength'])))
        mainIFD.tags.append(
            dngTag(Tag.ExposureTime, parseTag(self.etags['EXIF ExposureTime'])))
        mainIFD.tags.append(dngTag(Tag.DateTime, str(
            self.etags['EXIF DateTimeDigitized'])))
        mainIFD.tags.append(dngTag(Tag.PhotographicSensitivity, [
                            int(str(self.etags['EXIF ISOSpeedRatings']))]))
        mainIFD.tags.append(dngTag(Tag.Software, "PyDNG"))
        mainIFD.tags.append(dngTag(Tag.Orientation, [1]))
        mainIFD.tags.append(dngTag(Tag.DNGVersion, [1, 4, 0, 0]))
        mainIFD.tags.append(dngTag(Tag.DNGBackwardVersion, [1, 2, 0, 0]))
        mainIFD.tags.append(dngTag(Tag.UniqueCameraModel, camera_version))
        mainIFD.tags.append(dngTag(Tag.ColorMatrix1, ccm1))
        mainIFD.tags.append(dngTag(Tag.ColorMatrix2, ccm2))
        if fm:
            mainIFD.tags.append(dngTag(Tag.ForwardMatrix1, fm1))
            mainIFD.tags.append(dngTag(Tag.ForwardMatrix2, fm2))
        mainIFD.tags.append(dngTag(Tag.CameraCalibration1, camera_calibration))
        mainIFD.tags.append(dngTag(Tag.CameraCalibration2, camera_calibration))
        mainIFD.tags.append(dngTag(Tag.AsShotNeutral, as_shot_neutral))
        mainIFD.tags.append(dngTag(Tag.BaselineExposure, [[baseline_exp, 1]]))
        mainIFD.tags.append(dngTag(Tag.CalibrationIlluminant1, [ci1]))
        mainIFD.tags.append(dngTag(Tag.CalibrationIlluminant2, [ci2]))
        mainIFD.tags.append(dngTag(Tag.ProfileName, profile_name))
        mainIFD.tags.append(dngTag(Tag.ProfileEmbedPolicy, [profile_embed]))
        # mainIFD.tags.append(dngTag(Tag.ProfileToneCurve   , [0.0,0.0,1.0,1.0]))
        mainIFD.tags.append(dngTag(Tag.DefaultBlackRender, [0]))
        mainIFD.tags.append(dngTag(Tag.PreviewColorSpace, [2]))

        dngTemplate.IFDs.append(mainIFD)

        totalLength = dngTemplate.dataLen()

        mainTagStripOffset.setValue(
            [k for offset, k in dngTemplate.StripOffsets.items()])

        buf = bytearray(totalLength)
        dngTemplate.setBuffer(buf)
        dngTemplate.write()

        if file_output:
            outputDNG = image[:-4] + '.dng'
            outfile = open(outputDNG, "wb")
            outfile.write(buf)
            outfile.close()
            return outputDNG
        else:
            return buf


class RAW2DNG:
    def __init__(self):
        pass

    def __process__(self, rawImage, processing):

        if not processing:
            return rawImage

        elif isinstance(processing, types.FunctionType):

            processed = processing(rawImage)
            if not isinstance(processed, np.ndarray):
                raise TypeError("return value is not a valid numpy array!")
            elif processed.shape != rawImage.shape:
                raise ValueError("return array does not have the same shape!")

            return processed

        else:
            raise TypeError("process arguement is not a valid function!")

    def convert(self, image, tags, filename="image", path="", process=None, compress=False):
        dngTemplate = DNG()

        rawFrame = self.__process__(image, process)

        file_output = True

        width = tags.get(Tag.ImageWidth)[0]
        length = tags.get(Tag.ImageLength)[0]
        bpp = tags.get(Tag.BitsPerSample)[0]

        compression_scheme = 7 if compress else 1

        if compress:
            from ljpegCompress import pack16tolj
            tile = pack16tolj(rawFrame, int(width*2),
                              int(length/2), bpp, 0, 0, 0, "", 6)
        else:
            if bpp == 8:
                tile = rawFrame.astype('uint8').tobytes()
            elif bpp == 10:
                tile = pack10(rawFrame).tobytes()
            elif bpp == 12:
                tile = pack12(rawFrame).tobytes()
            elif bpp == 14:
                tile = pack14(rawFrame).tobytes()
            elif bpp == 16:
                tile = rawFrame.tobytes()

        dngTemplate.ImageDataStrips.append(tile)
        # set up the FULL IFD
        mainIFD = dngIFD()
        mainTagStripOffset = dngTag(
            Tag.TileOffsets, [0 for tile in dngTemplate.ImageDataStrips])
        mainIFD.tags.append(mainTagStripOffset)
        mainIFD.tags.append(dngTag(Tag.NewSubfileType, [0]))
        mainIFD.tags.append(dngTag(Tag.TileByteCounts, [len(
            tile) for tile in dngTemplate.ImageDataStrips]))
        mainIFD.tags.append(dngTag(Tag.Compression, [compression_scheme]))
        mainIFD.tags.append(dngTag(Tag.Software, "PyDNG"))

        for tag in tags.list():
            try:
                mainIFD.tags.append(dngTag(tag[0], tag[1]))
            except Exception as e:
                print("TAG Encoding Error!", e, tag)

        dngTemplate.IFDs.append(mainIFD)

        totalLength = dngTemplate.dataLen()

        mainTagStripOffset.setValue(
            [k for offset, k in dngTemplate.StripOffsets.items()])

        buf = bytearray(totalLength)
        dngTemplate.setBuffer(buf)
        dngTemplate.write()

        if file_output:
            if not filename.endswith(".dng"):
                filename = filename + '.dng'
            outputDNG = os.path.join(path, filename)
            with open(outputDNG, "wb") as outfile:
                outfile.write(buf)
            return outputDNG
        else:
            return buf


class DNGTags:
    def __init__(self):
        self.__tags__ = dict()

    def set(self, tag, value):
        if isinstance(value, int):
            self.__tags__[tag] = (value,)
        elif isinstance(value, float):
            self.__tags__[tag] = (value,)
        elif isinstance(value, str):
            self.__tags__[tag] = value
        elif len(value) > 1:
            self.__tags__[tag] = value
        else:
            self.__tags__[tag] = (value,)

    def get(self, tag):
        return self.__tags__[tag]

    def list(self):
        l = list()
        for k, v in self.__tags__.items():
            l.append((k, v))
        return l
