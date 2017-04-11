import struct, collections


class IFD:
    def __init__(self):
        self.name = ''
        self.subIFDs = []
        self.tags = {}
        self.offset = 0

    def printSubIFDs(self):
        for ifd in self.subIFDs:
            print("IFD tags (", len(ifd.tags), ")")
            ordered = collections.OrderedDict(sorted(ifd.tags.items()))
            for key, tag in ordered.iteritems():
                tag.printTAG()

    def getTag(self, tagName):
        return self.tags[DNG_TAGS_STR_ID[tagName]]


class TAG:
    def __init__(self):
        self.tell = 0
        self.tag = 0
        self.type = 0
        self.count = 0
        self.offset = 0
        self.value = []

    def readValue(self, rf):
        tell = rf.tell()
        rf.seek(self.offset)
        if self.type == 1:
            for j in range(0, self.count):
                (value,) = struct.unpack('B', rf.read(1))
                self.value.append(value)
        elif self.type == 2:
            (self.value,) = struct.unpack(str(self.count) + 's', rf.read(self.count))
        elif self.type == 3:
            for j in range(0, self.count):
                (value,) = struct.unpack('H', rf.read(2))
                self.value.append(value)
        elif self.type == 4:
            for j in range(0, self.count):
                (value,) = struct.unpack('I', rf.read(4))
                self.value.append(value)
        elif self.type == 5:
            for j in range(0, self.count):
                value = RATIONAL()
                (value.num,) = struct.unpack('I', rf.read(4))
                (value.denom,) = struct.unpack('I', rf.read(4))
                self.value.append(value)
        elif self.type == 6:
            for j in range(0, self.count):
                (value,) = struct.unpack('b', rf.read(1))
                self.value.append(value)
        elif self.type == 7:
            for j in range(0, self.count):
                (value,) = struct.unpack('b', rf.read(1))
                self.value.append(value)
        elif self.type == 8:
            for j in range(0, self.count):
                (value,) = struct.unpack('h', rf.read(2))
                self.value.append(value)
        elif self.type == 9:
            for j in range(0, self.count):
                (value,) = struct.unpack('i', rf.read(4))
                self.value.append(value)
        elif self.type == 10:
            for j in range(0, self.count):
                value = RATIONAL()
                (value.num,) = struct.unpack('i', rf.read(4))
                (value.denom,) = struct.unpack('i', rf.read(4))
                self.value.append(value)
        elif self.type == 11:
            for j in range(0, self.count):
                (value,) = struct.unpack('f', rf.read(4))
                self.value.append(value)
        elif self.type == 12:
            for j in range(0, self.count):
                (value,) = struct.unpack('d', rf.read(8))
                self.value.append(value)
        else:
            print("DATA TYPE ", self.type, " NOT SUPPORTED!")
        rf.seek(tell)

    def writeTAG(self, wf):
        tell = wf.tell()
        if self.type == 1:
            for j in range(0, self.count):
                wf.write(struct.pack('B', self.value[j]))
        elif self.type == 2:
            # wf.write(struct.pack(str(self.count)+'s',self.value))
            pass
        elif self.type == 3:
            for j in range(0, self.count):
                wf.write(struct.pack('H', self.value[j]))
        elif self.type == 4:
            for j in range(0, self.count):
                wf.write(struct.pack('I', self.value[j]))
        elif self.type == 5:
            for j in range(0, self.count):
                wf.write(struct.pack('I', self.value[j].num))
                wf.write(struct.pack('I', self.value[j].denom))
        elif self.type == 6:
            for j in range(0, self.count):
                wf.write(struct.pack('b', self.value[j]))
        elif self.type == 7:
            for j in range(0, self.count):
                wf.write(struct.pack('b', self.value[j]))
        elif self.type == 8:
            for j in range(0, self.count):
                wf.write(struct.pack('h', self.value[j]))
        elif self.type == 9:
            for j in range(0, self.count):
                wf.write(struct.pack('i', self.value[j]))
        elif self.type == 10:
            for j in range(0, self.count):
                wf.write(struct.pack('i', self.value[j].num))
                wf.write(struct.pack('i', self.value[j].denom))
        elif self.type == 11:
            for j in range(0, self.count):
                wf.write(struct.pack('f', self.value[j]))
        elif self.type == 12:
            for j in range(0, self.count):
                wf.write(struct.pack('d', self.value[j]))
        else:
            print("ERROR: UNKNOWN TAG TYPE TO PRINT")
        currentTell = wf.tell()
        wf.seek(self.offset)
        self.offset = tell
        wf.write(struct.pack('I', self.offset))
        wf.seek(currentTell)

    def printTAG(self):
        try:
            print("Tag: ", DNG_TAGS_ID_STR[self.tag], ":", self.tag, ", ", self.type, ", ", self.count, ", ", self.offset, ",", self.tell, ", ", self.value)
        except KeyError:
            print("Invalid key: ", self.tag)


class RATIONAL:
    def __init__(self):
        self.num = 1
        self.denom = 1

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return str(self.num) + "/" + str(self.denom)


DNG_TAGS_STR_ID = {
    'NewSubfileType': 254,
    'ImageWidth': 256,
    'ImageLength': 257,
    'BitsPerSample': 258,
    'Compression': 259,
    'PhotometricInterpretation': 262,
    'Make': 271,
    'Model': 272,
    'StripOffsets': 273,
    'Orientation': 274,
    'SamplesPerPixel': 277,
    'RowsPerStrip': 278,
    'StripByteCounts': 279,
    'PlanarConfiguration': 284,
    'Software': 305,
    'DateTime': 306,
    'TileWidth': 322,
    'TileLength': 323,
    'TileOffsets': 324,
    'TileByteCounts': 325,
    'SubIFDs': 330,
    'YCbCrCoefficients': 529,
    'YCbCrSubSampling': 530,
    'YCbCr': 531,
    'ReferenceBlackWhite': 532,
    'Unknown1': 700,
    'CFARepeatPatternDim': 33421,
    'CFAPattern': 33422,
    'Unknown2': 34665,
    'DNGVersion': 50706,
    'DNGBackwardVersion': 50707,
    'UniqueCameraModel': 50708,
    'CFAPlaneColor': 50710,
    'CFALayout': 50711,
    'BlackLevelRepeatDim': 50713,
    'BlackLevel': 50714,
    'WhiteLevel': 50717,
    'DefaultScale': 50718,
    'DefaultCropOrigin': 50719,
    'DefaultCropSize': 50720,
    'ColorMatrix1': 50721,
    'ColorMatrix2': 50722,
    'CameraCalibration1': 50723,
    'CameraCalibration2': 50724,
    'AnalogBalance': 50727,
    'AsShotNeutral': 50728,
    'BaselineExposure': 50730,
    'BaselineNoise': 50731,
    'BaselineSharpness': 50732,
    'BayerGreenSplit': 50733,
    'LinearResponseLimit': 50734,
    'LensInfo': 50736,
    'AntiAliasStrength': 50738,
    'ShadowScale': 50739,
    'DNGPrivateData': 50740,
    'CalibrationIlluminant1': 50778,
    'CalibrationIlluminant2': 50779,
    'BestQualityScale': 50780,
    'RawDataUniqueID': 50781,
    'OriginalRawFileName': 50827,
    'ActiveArea': 50829,
    'CameraCalibrationSignature': 50931,
    'ProfileCalibrationSignature': 50932,
    'ProfileName': 50936,
    'ProfileToneCurve': 50940,
    'ProfileEmbedPolicy': 50941,
    'ProfileCopyright': 50942,
    'ForwardMatrix1': 50964,
    'ForwardMatrix2': 50965,
    'PreviewApplicationName': 50966,
    'PreviewApplicationVersion': 50967,
    'PreviewSettingsDigest': 50969,
    'PreviewColorSpace': 50970,
    'PreviewDateTime': 50971,
    'ProfileLookTableDims': 50981,
    'ProfileLookTableData': 50982,
    'NoiseProfile': 51041,
    'Unknown3': 51111
}

DNG_TAGS_ID_STR = {}
