#!/usr/bin/python2.7
# https://github.com/krontech/chronos-utils/tree/master/python_raw2dng

# standard python imports
import sys
import struct
import os, io
import time
import array
import getopt
import platform
import errno
import numpy as np
import bitunpack

class Type:
    # TIFF Type Format = (Tag TYPE value, Size in bytes of one instance)
    Invalid = (0,0) # Should not be used
    Byte = (1,1) # 8-bit unsigned
    Ascii = (2,1) # 7-bit ASCII code
    Short = (3,2) # 16-bit unsigned
    Long = (4,4) # 32-bit unsigned
    Rational = (5,8) # 2 Longs, numerator:denominator
    Sbyte = (6,1) # 8 bit signed integer
    Undefined = (7,1) # 8 bit byte containing anything
    Sshort = (8,2) # 16 bit signed
    Slong = (9,4) # 32 bit signed
    Srational = (10,8) # 2 Slongs, numerator:denominator
    Float = (11,4) # 32bit float IEEE
    Double = (12,8) # 64bit double IEEE
    IFD = (13,4) # IFD (Same as Long)

Types = [(getattr(Type,n),n) for n in dir(Type) if n!="__doc__" and n!="__module__"]
Types.sort()

class Tag:
    Invalid                     = (0,Type.Invalid)
    # TIFF/DNG/EXIF/CinemaDNG Tag Format = (TAG value, Tag Type)
    NewSubfileType              = (254,Type.Long)
    ImageWidth                  = (256,Type.Long)
    ImageLength                 = (257,Type.Long)
    BitsPerSample               = (258,Type.Short)
    Compression                 = (259,Type.Short)
    PhotometricInterpretation   = (262,Type.Short)
    FillOrder                   = (266,Type.Short)
    ImageDescription            = (270,Type.Ascii)
    Make                        = (271,Type.Ascii)
    Model                       = (272,Type.Ascii)
    StripOffsets                = (273,Type.Long)
    Orientation                 = (274,Type.Short)
    SamplesPerPixel             = (277,Type.Short)
    RowsPerStrip                = (278,Type.Short)
    StripByteCounts             = (279,Type.Long)
    XResolution                 = (282,Type.Rational)
    YResolution                 = (283,Type.Rational)
    PlanarConfiguration         = (284,Type.Short)
    ResolutionUnit              = (296,Type.Short)
    Software                    = (305,Type.Ascii)
    DateTime                    = (306,Type.Ascii)
    Artist                      = (315,Type.Ascii)
    TileWidth                   = (322,Type.Short)
    TileLength                  = (323,Type.Short)
    TileOffsets                 = (324,Type.Long)
    TileByteCounts              = (325,Type.Long)
    SubIFD                      = (330,Type.IFD)
    XMP_Metadata                = (700,Type.Undefined)
    CFARepeatPatternDim         = (33421,Type.Short)
    CFAPattern                  = (33422,Type.Byte)
    Copyright                   = (33432,Type.Ascii)
    ExposureTime                = (33434,Type.Rational)
    FNumber                     = (33437,Type.Rational)
    EXIF_IFD                    = (34665,Type.IFD)
    ExposureProgram             = (34850,Type.Short)
    PhotographicSensitivity     = (34855,Type.Short)
    SensitivityType             = (34864,Type.Short)
    ExifVersion                 = (36864,Type.Undefined)
    DateTimeOriginal            = (36867,Type.Ascii)
    ShutterSpeedValue           = (37377,Type.Srational)
    ApertureValue               = (37378,Type.Rational)
    ExposureBiasValue           = (37380,Type.Srational)
    MaxApertureValue            = (37381,Type.Rational)
    SubjectDistance             = (37382,Type.Rational)
    MeteringMode                = (37383,Type.Short)
    Flash                       = (37385,Type.Short)
    FocalLength                 = (37386,Type.Rational)
    TIFF_EP_StandardID          = (37398,Type.Byte)
    SubsecTime                  = (37520,Type.Ascii)
    SubsecTimeOriginal          = (37521,Type.Ascii)
    FocalPlaneXResolution       = (41486,Type.Rational)
    FocalPlaneYResolution       = (41487,Type.Rational)
    FocalPlaneResolutionUnit    = (41488,Type.Short)
    FocalLengthIn35mmFilm       = (41989,Type.Short)
    EXIFPhotoBodySerialNumber   = (42033,Type.Ascii)
    EXIFPhotoLensModel          = (42036,Type.Ascii)
    DNGVersion                  = (50706,Type.Byte)
    DNGBackwardVersion          = (50707,Type.Byte)
    UniqueCameraModel           = (50708,Type.Ascii)
    CFAPlaneColor               = (50710,Type.Byte)
    CFALayout                   = (50711,Type.Short)
    LinearizationTable          = (50712,Type.Short)
    BlackLevelRepeatDim         = (50713,Type.Short)
    BlackLevel                  = (50714,Type.Short)
    WhiteLevel                  = (50717,Type.Short)
    DefaultScale                = (50718,Type.Rational)
    DefaultCropOrigin           = (50719,Type.Long)
    DefaultCropSize             = (50720,Type.Long)
    ColorMatrix1                = (50721,Type.Srational)
    ColorMatrix2                = (50722,Type.Srational)
    CameraCalibration1          = (50723,Type.Srational)
    CameraCalibration2          = (50724,Type.Srational)
    AnalogBalance               = (50727,Type.Rational)
    AsShotNeutral               = (50728,Type.Rational)
    BaselineExposure            = (50730,Type.Srational)
    BaselineNoise               = (50731,Type.Rational)
    BaselineSharpness           = (50732,Type.Rational)
    BayerGreenSplit             = (50733,Type.Long)
    LinearResponseLimit         = (50734,Type.Rational)
    CameraSerialNumber          = (50735,Type.Ascii)
    AntiAliasStrength           = (50738,Type.Rational)
    ShadowScale                 = (50739,Type.Rational)
    DNGPrivateData              = (50740,Type.Byte)
    MakerNoteSafety             = (50741,Type.Short)
    CalibrationIlluminant1      = (50778,Type.Short)
    CalibrationIlluminant2      = (50779,Type.Short)
    BestQualityScale            = (50780,Type.Rational)
    RawDataUniqueID             = (50781,Type.Byte)
    ActiveArea                  = (50829,Type.Long)
    CameraCalibrationSignature  = (50931,Type.Ascii)
    ProfileCalibrationSignature = (50932,Type.Ascii)
    NoiseReductionApplied       = (50935,Type.Rational)
    ProfileName                 = (50936,Type.Ascii)
    ProfileHueSatMapDims        = (50937,Type.Long)
    ProfileHueSatMapData1       = (50938,Type.Float)
    ProfileHueSatMapData2       = (50939,Type.Float)
    ProfileEmbedPolicy          = (50941,Type.Long)
    PreviewApplicationName      = (50966,Type.Ascii)
    PreviewApplicationVersion   = (50967,Type.Ascii)
    PreviewSettingsDigest       = (50969,Type.Byte)
    PreviewColorSpace           = (50970,Type.Long)
    PreviewDateTime             = (50971,Type.Ascii)
    NoiseProfile                = (51041,Type.Double)
    TimeCodes                   = (51043,Type.Byte)
    FrameRate                   = (51044,Type.Srational)
    OpcodeList1                 = (51008,Type.Undefined)
    OpcodeList2                 = (51009,Type.Undefined)
    ReelName                    = (51081,Type.Ascii)
    BaselineExposureOffset      = (51109,Type.Srational) # 1.4 Spec says rational but mentions negative values?
    NewRawImageDigest           = (51111,Type.Byte)

IfdNames = [n for n in dir(Tag) if n!="__doc__" and n!="__module__"]
IfdValues = [getattr(Tag,n) for n in IfdNames]
IfdIdentifiers = [getattr(Tag,n)[0] for n in IfdNames]
IfdTypes = [getattr(Tag,n)[1][0] for n in IfdNames]
IfdLookup = dict(zip(IfdIdentifiers,IfdNames))

class dngHeader(object):
    def __init__(self):
        self.IFDOffset = 8

    def raw(self):
        return struct.pack("<sI", "II\x2A\x00", self.IFDOffset)

class dngTag(object):
    def __init__(self, tagType=Tag.Invalid, value=[]):
        self.Type = tagType
        self.TagId = tagType[0]
        self.DataType = tagType[1]
        self.DataCount = len(value)
        self.DataOffset = 0

        self.subIFD = None
        
        # encode the given data
        self.setValue(value)
        
        self.DataLength = len(self.Value)

        if (self.DataLength <= 4): self.selfContained = True
        else:                      self.selfContained = False

    def setValue(self, value):
        if   self.DataType == Type.Byte:      self.Value = struct.pack('<%sB' % len(value), *value)
        elif self.DataType == Type.Short:     self.Value = struct.pack('<%sH' % len(value), *value)
        elif self.DataType == Type.Long:      self.Value = struct.pack('<%sL' % len(value), *value)
        elif self.DataType == Type.Sbyte:     self.Value = struct.pack('<%sb' % len(value), *value)
        elif self.DataType == Type.Undefined: self.Value = struct.pack('<%sB' % len(value), *value)
        elif self.DataType == Type.Sshort:    self.Value = struct.pack('<%sh' % len(value), *value)
        elif self.DataType == Type.Slong:     self.Value = struct.pack('<%sl' % len(value), *value)
        elif self.DataType == Type.Float:     self.Value = struct.pack('<%sf' % len(value), *value)
        elif self.DataType == Type.Double:    self.Value = struct.pack('<%sd' % len(value), *value)
        elif self.DataType == Type.Rational:  self.Value = struct.pack('<%sL' % (len(value)*2), *[item for sublist in value for item in sublist]) # ... This... uhm... flattens the list of two value pairs
        elif self.DataType == Type.Srational: self.Value = struct.pack('<%sl' % (len(value)*2), *[item for sublist in value for item in sublist])
        elif self.DataType == Type.Ascii:
            self.Value = struct.pack('<%scx0L' % len(value), *value)
            self.DataCount += 1
        elif self.DataType == Type.IFD:
            self.Value = "\x00\x00\x00\x00"
            self.subIFD = value[0]
        self.Value += '\x00'*(((len(self.Value)+3) & 0xFFFFFFFC) - len(self.Value))
        

    def setBuffer(self, buf, tagOffset, dataOffset):
        self.buf = buf
        self.TagOffset = tagOffset
        self.DataOffset = dataOffset
        if self.subIFD:
            #print "subIDF: 0x%08X, 0x%08X" % (self.TagOffset, self.DataOffset)
            self.subIFD.setBuffer(buf, self.DataOffset)
            
    def dataLen(self):
        if self.subIFD:
            return self.subIFD.dataLen()
        if self.selfContained:
            return 0
        else:
            return (len(self.Value) + 3) & 0xFFFFFFFC
        
    def write(self):
        if not self.buf:
            raise RuntimeError("buffer not initialized")

        #if not self.subIFD:
        #    print "Tag: %04X - 0x%08X, 0x%08X - %-30s %s" % (self.TagId, self.TagOffset, self.DataOffset, IfdLookup.get(self.TagId,"Unknown"), self.Value.encode('hex'))
        
        if self.subIFD:
            self.subIFD.write()
            tagData = struct.pack("<HHII", self.TagId, Type.Long[0], self.DataCount, self.DataOffset)
            struct.pack_into("<12s", self.buf, self.TagOffset, tagData)
        else:
            if self.selfContained:
                tagData = struct.pack("<HHI4s", self.TagId, self.DataType[0], self.DataCount, self.Value)
                struct.pack_into("<12s", self.buf, self.TagOffset, tagData)
            else:
                tagData = struct.pack("<HHII", self.TagId, self.DataType[0], self.DataCount, self.DataOffset)
                struct.pack_into("<12s", self.buf, self.TagOffset, tagData)
                struct.pack_into("<%ds" % (self.DataLength), self.buf, self.DataOffset, self.Value)
            
        
class dngIFD(object):
    def __init__(self):
        self.tags = []
        self.NextIFDOffset = 0

    def setBuffer(self, buf, offset):
        self.buf = buf
        self.offset = offset
        currentDataOffset = offset + 2 + len(self.tags)*12 + 4
        currentTagOffset = offset + 2
        for tag in sorted(self.tags, key=lambda x: x.TagId):
            tag.setBuffer(buf, currentTagOffset, currentDataOffset)
            currentTagOffset += 12
            currentDataOffset += tag.dataLen()
            #currentDataOffset = (currentDataOffset + 3) & 0xFFFFFFFC
            

    def dataLen(self):
        totalLength = 2 + len(self.tags)*12 + 4
        for tag in sorted(self.tags, key=lambda x: x.TagId):
            totalLength += tag.dataLen()
        return (totalLength + 3) & 0xFFFFFFFC

    def write(self):
        if not self.buf:
            raise RuntimeError("buffer not initialized")

        struct.pack_into("<H", self.buf, self.offset, len(self.tags))

        for tag in sorted(self.tags, key=lambda x: x.TagId):
            tag.write()

        #print "IDF: 0x%08X" % (self.offset)
        struct.pack_into("<I", self.buf, self.offset + 2 + len(self.tags)*12, self.NextIFDOffset)


class DNG(object):
    def __init__(self):
        self.IFDs = []
        self.ImageDataStrips = []
        self.StripOffsets = {}

    def setBuffer(self, buf):
        self.buf = buf

        currentOffset = 8

        for ifd in self.IFDs:
            ifd.setBuffer(buf, currentOffset)
            currentOffset += ifd.dataLen()
            

    def dataLen(self):
        totalLength = 8
        for ifd in self.IFDs:
            totalLength += (ifd.dataLen() + 3) & 0xFFFFFFFC

        for i in range(len(self.ImageDataStrips)):
            self.StripOffsets[i] = totalLength
            strip = self.ImageDataStrips[i]
            totalLength += (len(strip) + 3) & 0xFFFFFFFC
            
        return (totalLength + 3) & 0xFFFFFFFC

    def write(self):
        struct.pack_into("<ccbbI", self.buf, 0, 'I', 'I', 0x2A, 0x00, 8) # assume the first IFD happens immediately after header

        for ifd in self.IFDs:
            ifd.write()

        for i in range(len(self.ImageDataStrips)):
            self.buf[self.StripOffsets[i]:self.StripOffsets[i]+len(self.ImageDataStrips[i])] = self.ImageDataStrips[i]


def creation_date(path_to_file):
    """
    Try to get the date that a file was created, falling back to when it was
    last modified if that isn't possible.
    See http://stackoverflow.com/a/39501288/1709587 for explanation.
    """
    if platform.system() == 'Windows':
        return os.path.getctime(path_to_file)
    else:
        stat = os.stat(path_to_file)
        try:
            return stat.st_birthtime
        except AttributeError:
            # We're probably on Linux. No easy way to get creation dates here,
            # so we'll settle for when its content was last modified.
            return stat.st_mtime


def process(input_file):
    def extractRAW(img):
        file = open(img, 'rb')

        stream = io.BytesIO(file.read())

        ver = 2
        offset = {
            1: 6404096,
            2: 10270208,
        }[2]

        data = stream.getvalue()[-offset:]
        # assert data[:4] == 'BRCM'
        data = data[32768:]
        data = np.fromstring(data, dtype=np.uint8)

        reshape, crop = {
            1: ((1952, 3264), (1944, 3240)),
            2: ((2480, 4128), (2464, 4100)),
        }[ver]
        data = data.reshape(reshape)[:crop[0], :crop[1]]

        data = data.astype(np.uint16) << 2
        for byte in range(4):
            data[:, byte::5] |= ((data[:, 4::5] >> ((4 - byte) * 2)) & 0b11)
        data = np.delete(data, np.s_[4::5], 1)

        return data

    # extract bayer raw to 16bit numpy array
    rawImage = extractRAW(input_file)
    # rawImage = np.rot90(rawImage, 2)

    # lens shade frame
    shading = np.fromfile('shade/shade_sun', dtype=np.uint16)
    shading = np.reshape(shading, rawImage.shape)

    # dark frame
    dark = np.fromfile('dark/dark_frame', dtype=np.uint16)
    dark = np.reshape(dark, rawImage.shape)

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

    awb = [1.00434991, 1.60903256, 1.0]
    rawImage[1::2, 0::2] = rawImage[1::2, 0::2] * awb[0]
    rawImage[0::2, 0::2] = rawImage[0::2, 0::2] * awb[1]
    rawImage[1::2, 1::2] = rawImage[1::2, 1::2] * awb[1]

    if np.amin(pm) < 1023:
        rawImage = np.clip(rawImage, 0, np.amin(pm))
    else:
        rawImage = np.clip(rawImage, 0, 1023)

    print(pm, 1023/pm)
    print(np.amax(rawImage), np.amin(rawImage))

    rawImage = rawImage.astype(np.uint16)
    return rawImage


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

def blockshaped(arr, nrows, ncols):
    """
    Return an array of shape (n, nrows, ncols) where
    n * nrows * ncols = arr.size

    If arr is a 2D array, the returned array should look like n subblocks with
    each subblock preserving the "physical" layout of arr.
    """
    h, w = arr.shape
    return (arr.reshape(h//nrows, nrows, -1, ncols)
               .swapaxes(1,2)
               .reshape(-1, nrows, ncols))


def convert(inputFilename, outputFilenameFormat, width, length, colour, bpp):
    dngTemplate = DNG()

    creationTime = creation_date(inputFilename)
    creationTimeString = time.strftime("%x %X", time.localtime(creationTime))

    # set up the image binary data
    # 410,352
    rawFrame = process(inputFilename)
    tw = 410
    th = 352
    tiles = blockshaped(rawFrame, th,tw)
    for tile in tiles:
        d = tile.tostring()
        w = tile.shape[1]
        h = tile.shape[0]
        tile1 = bitunpack.pack16tolj(d,w,h/2,16,0,w/2,w/2,"")
        tile2 = bitunpack.pack16tolj(d,w,h/2,16,w,w/2,w/2,"")
        dngTemplate.ImageDataStrips.append(tile1)
        dngTemplate.ImageDataStrips.append(tile2)
    
    # rawdata = rawFrame.tostring()
    # https://bitbucket.org/baldand/mlrawviewer/src/e7abaaf4cf9be66f46e0c8844297be0e7d88c288/bitunpack.c?at=master&fileviewer=file-view-default


    # set up the FULL IFD
    mainIFD = dngIFD()
    mainTagStripOffset = dngTag(Tag.TileOffsets, [0 for tile in dngTemplate.ImageDataStrips])
    mainIFD.tags.append(mainTagStripOffset)
    mainIFD.tags.append(dngTag(Tag.NewSubfileType           , [0]))
    mainIFD.tags.append(dngTag(Tag.TileByteCounts          , [len(tile) for tile in dngTemplate.ImageDataStrips]))
    mainIFD.tags.append(dngTag(Tag.ImageWidth               , [width]))
    mainIFD.tags.append(dngTag(Tag.ImageLength              , [length]))
    mainIFD.tags.append(dngTag(Tag.SamplesPerPixel          , [1]))
    mainIFD.tags.append(dngTag(Tag.BitsPerSample            , [16]))
    mainIFD.tags.append(dngTag(Tag.TileWidth             , [tw/2]))
    mainIFD.tags.append(dngTag(Tag.TileLength             , [th]))
    mainIFD.tags.append(dngTag(Tag.Compression              , [7])) 
    mainIFD.tags.append(dngTag(Tag.PhotometricInterpretation, [32803])) 
    mainIFD.tags.append(dngTag(Tag.CFARepeatPatternDim      , [2, 2]))
    mainIFD.tags.append(dngTag(Tag.CFAPattern               , [2, 1, 1, 0]))
    mainIFD.tags.append(dngTag(Tag.BlackLevel               , [np.amin(rawFrame)]))
    mainIFD.tags.append(dngTag(Tag.WhiteLevel               , [np.amax(rawFrame)]))
    mainIFD.tags.append(dngTag(Tag.Make                     , "Camera V2"))
    mainIFD.tags.append(dngTag(Tag.Model                    , "IMX219"))
    # mainIFD.tags.append(dngTag(Tag.DateTime                 , [creationTimeString]))
    mainIFD.tags.append(dngTag(Tag.Software                 , "pydng"))
    mainIFD.tags.append(dngTag(Tag.Orientation              , [1]))
    mainIFD.tags.append(dngTag(Tag.DNGVersion               , [1, 4, 0, 0]))
    mainIFD.tags.append(dngTag(Tag.DNGBackwardVersion       , [1, 2, 0, 0]))
    mainIFD.tags.append(dngTag(Tag.UniqueCameraModel        , "RaspberryPi Camera V2"))
    mainIFD.tags.append(dngTag(Tag.ColorMatrix1             , [[19549, 10000], [-7877, 10000], [-2582, 10000],	
                                                               [-5724, 10000], [10121, 10000], [1917, 10000],
                                                               [-1267, 10000], [ -110, 10000], [ 6621, 10000]]))
    mainIFD.tags.append(dngTag(Tag.ColorMatrix2             , [[13244, 10000], [-5501, 10000], [-1248, 10000],	
                                                               [-1508, 10000], [9858, 10000], [1935, 10000],
                                                               [-270, 10000], [ -1083, 10000], [ 4366, 10000]]))

    mainIFD.tags.append(dngTag(Tag.NoiseProfile   , [0.000393625,0.000000122976 ]))
    mainIFD.tags.append(dngTag(Tag.CalibrationIlluminant1   , [1]))
    mainIFD.tags.append(dngTag(Tag.CalibrationIlluminant2   , [23]))
    mainIFD.tags.append(dngTag(Tag.PreviewColorSpace   , [2]))

    dngTemplate.IFDs.append(mainIFD)

    totalLength = dngTemplate.dataLen()
    # this must happen after dataLen is calculated! (dataLen caches the offsets)

    mainTagStripOffset.setValue([k for offset,k in dngTemplate.StripOffsets.items()])

    buf = bytearray(totalLength)
    dngTemplate.setBuffer(buf)
    dngTemplate.write()

    outputDNG = inputFilename.strip('.jpg') + '.dng'

    outfile = open(outputDNG, "wb")
    outfile.write(buf)
    outfile.close()


def main():
    width = 3280
    length = 2464
    colour = True
    inputFilename = None
    outputFilenameFormat = None
    bpp = 16
    
    try:
        options, args = getopt.getopt(sys.argv[1:], 'CMpw:l:h:',
            ['help', 'color', 'packed', 'mono', 'width', 'length', 'height', 'oldpack'])
    except getopt.error:
        print 'Error: You tried to use an unknown option.\n\n'
        print helptext
        sys.exit(0)
        
    if len(sys.argv[1:]) == 0:
        print helptext
        sys.exit(0)
    
    for o, a in options:
        if o in ('--help'):
            print helptext
            sys.exit(0)
        
        elif o in ('-l', '-h', '--length', '--height'):
            length = int(a)

        elif o in ('-w', '--width'):
            width = int(a)

    if len(args) < 1:
        print helptext
        sys.exit(0)

    elif len(args) == 1:
        inputFilename = args[0]
        dirname = os.path.splitext(inputFilename)[0]
        basename = os.path.basename(inputFilename)
        print basename
        outputFilenameFormat = dirname + '/frame_%06d.DNG'
    else:
        inputFilename = args[0]
        outputFilenameFormat = args[1]

    convert(inputFilename, outputFilenameFormat, width, length, colour, bpp)

if __name__ == "__main__":
    main()

        
        
