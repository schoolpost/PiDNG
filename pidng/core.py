import os
import numpy as np

from .dng import Type, Tag, dngHeader, dngIFD, dngTag, DNG
from .legacy import *
from .defs import *

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
    return out

class DNGTags:
    def __init__(self):
        self.__tags__ = dict()

    def set(self, tag : Tag, value):        
        if isinstance(value, int):
            self.__tags__[tag] = dngTag(tag, [value])
        else:
            self.__tags__[tag] = dngTag(tag, value)

    def get(self, tag):
        try:
            return self.__tags__[tag]
        except KeyError:
            return None

    def list(self):
        l = list()
        for k, v in self.__tags__.items():
            l.append(v)
        return l

class DNGBASE:
    def __init__(self):
        pass
    
    def __data_condition__(self, data : np.ndarray):
        if data.dtype != np.uint16:
            raise Exception("RAW Data is not in correct format. Must be 16bit Numpy Array. ")

    def __tags_condition__(self, tags : DNGTags):
        if not tags.get(Tag.ImageWidth):
            raise Exception("No width is defined in tags.")
        if not tags.get(Tag.ImageLength):
            raise Exception("No height is defined in tags.")
        if not tags.get(Tag.BitsPerSample):
            raise Exception("Bit per pixel is not defined.")        


    def __process__(self, rawFrame : np.ndarray, tags: DNGTags, compress : bool) -> bytearray:

        width = tags.get(Tag.ImageWidth).rawValue[0]
        length = tags.get(Tag.ImageLength).rawValue[0]
        bpp = tags.get(Tag.BitsPerSample).rawValue[0]

        compression_scheme = Compression.LJ92 if compress else Compression.Uncompressed

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
        
        dngTemplate = DNG()

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
        mainIFD.tags.append(dngTag(Tag.Software, "PiDNG"))

        for tag in tags.list():
            try:
                mainIFD.tags.append(tag)
            except Exception as e:
                print("TAG Encoding Error!", e, tag)

        dngTemplate.IFDs.append(mainIFD)

        totalLength = dngTemplate.dataLen()

        mainTagStripOffset.setValue(
            [k for offset, k in dngTemplate.StripOffsets.items()])

        buf = bytearray(totalLength)
        dngTemplate.setBuffer(buf)
        dngTemplate.write()

        return buf

    def convert(self, image : np.ndarray, tags : DNGTags, filename : str, path : str, compress=False):
        
        # valdify incoming data
        self.__data_condition__(image)
        self.__tags_condition__(tags)
        buf = self.__process__(image, tags, compress)

        file_output = False
        if len(filename) > 0:
            file_output = True

        if file_output:
            if not filename.endswith(".dng"):
                filename = filename + '.dng'
            outputDNG = os.path.join(path, filename)
            with open(outputDNG, "wb") as outfile:
                outfile.write(buf)
            return outputDNG
        else:
            return buf


class RAW2DNG(DNGBASE):
    def __init__(self):
        super().__init__()


class RPI2DNG(DNGBASE):
    def __init__(self):
        super().__init__()
        self.model = None
        
    def __unpack_pixels__(data : np.ndarray) -> np.ndarray:
        return np.ndarray()

class RASPIRAW2DNG(DNGBASE):
    def __init__(self):
        super().__init__()

