import struct, collections
import numpy as np
from DNGTags import *
from multiprocessing import Pool
import multiprocessing
import itertools


class DNG:
    def __init__(self, read_file):
        self.read_file = read_file
        self.ifd = IFD()

    def openDNG(self):
        self.rf = open(self.read_file, mode='rb')

    def readFullDNG(self):
        self.openDNG()
        self.readHeader()
        self.readIFDs()
        self.readSubIFD('SubIFDs')

    def writeDNG(self, write_file):
        self.write_file = write_file
        self.wf = open(self.write_file, mode='wb')
        self.writeHeader()
        self.writeIFD(self.ifd)

    def readHeader(self):
        self.rf.seek(0)
        self.endian = self.rf.read(2)
        if self.endian != 'II':
            quit()
        # print "Endian: ", self.endian
        (self.magicNum,) = struct.unpack('h', self.rf.read(2))
        if self.magicNum != 42:
            quit()
            # print "Successfully read header."

    def writeHeader(self):
        self.wf.write(struct.pack('2s', self.endian))
        self.wf.write(struct.pack('H', self.magicNum))
        self.wf.write(struct.pack('I', 8))

    def writeIFD(self, ifd):
        self.wf.write(struct.pack('H', len(ifd.tags)))
        sortedTags = sorted(ifd.tags.iterkeys())
        tagsToWriteOffset = []

        try:
            subIFDTag = ifd.tags[DNG_TAGS_STR_ID['SubIFDs']]
            subIFDTag.count = len(ifd.subIFDs)
        except KeyError:
            pass

        for key in sortedTags:
            tag = ifd.tags[key]
            self.wf.write(struct.pack('H', tag.tag))
            self.wf.write(struct.pack('H', tag.type))
            self.wf.write(struct.pack('I', tag.count))
            tag.offset = self.wf.tell()
            if tag.type == 1 and tag.count <= 4:
                for j in range(0, 4):
                    self.wf.write(struct.pack('B', tag.value[j]))
            elif tag.type == 3 and tag.count <= 2:
                for j in range(0, 2):
                    self.wf.write(struct.pack('H', tag.value[j]))
            elif tag.type == 4 and tag.count == 1:
                self.wf.write(struct.pack('I', tag.value[0]))
            elif tag.type == 6 and tag.count <= 4:
                for j in range(0, 4):
                    self.wf.write(struct.pack('b', tag.value[j]))
            elif tag.type == 7 and tag.count <= 4:
                for j in range(0, 4):
                    self.wf.write(struct.pack('b', tag.value[j]))
            elif tag.type == 8 and tag.count <= 2:
                for j in range(0, 2):
                    self.wf.write(struct.pack('h', tag.value[j]))
            elif tag.type == 9 and tag.count == 1:
                self.wf.write(struct.pack('i', tag.value[0]))
            elif tag.type == 11 and tag.count == 1:
                self.wf.write(struct.pack('f', tag.value[0]))
            else:
                # tag.offset = self.wf.tell()
                tagsToWriteOffset.append(tag)
                self.wf.write(struct.pack('I', tag.offset))
        # Last IFD tag
        self.wf.write(struct.pack('I', 0))
        for tag in tagsToWriteOffset:
            tag.writeTAG(self.wf)
        if (hasattr(ifd, 'image')):
            self.writeImageStrips(ifd)
        try:
            subIFDTag = ifd.tags[DNG_TAGS_STR_ID['SubIFDs']]
            subTagNum = 0
            for subIFD in ifd.subIFDs:
                preTell = self.wf.tell()
                self.writeIFD(subIFD)
                currentTell = self.wf.tell()
                self.wf.seek(subIFDTag.offset + 4 * subTagNum)
                self.wf.write(struct.pack('I', preTell))
                self.wf.seek(currentTell)
                subTagNum += 1
        except KeyError:
            pass

    def readIFDs(self):
        (self.ifd.offset,) = struct.unpack('I', self.rf.read(4))
        self.readIFDFromOffset(self.ifd.tags, self.ifd.offset)
        try:
            if self.ifd.getTag('StripByteCounts').count > 0:
                self.readImageStrips(self.ifd)
        except KeyError:
            pass

    def readSubIFD(self, strTag):
        try:
            tag = self.ifd.tags[DNG_TAGS_STR_ID[strTag]]
        except KeyError:
            return

        if tag.count == 1:
            ifd1 = IFD()
            ifd1.offset = tag.value[0]
            self.ifd.subIFDs.append(ifd1)
            self.readIFDFromOffset(ifd1.tags, tag.value[0])
            # self.readImageStrips(ifd1)
        else:
            # Multiple Sub IFDs
            # TODO: Add support for any number of Sub IFDs and make recursive
            self.rf.seek(tag.offset)
            (subIFDOffset1,) = struct.unpack('I', self.rf.read(4))
            (subIFDOffset2,) = struct.unpack('I', self.rf.read(4))

            ifd1 = IFD()
            ifd1.offset = subIFDOffset1
            ifd2 = IFD()
            ifd2.offset = subIFDOffset2
            self.ifd.subIFDs.append(ifd1)
            self.ifd.subIFDs.append(ifd2)

            self.readIFDFromOffset(ifd1.tags, subIFDOffset1)
            self.readIFDFromOffset(ifd2.tags, subIFDOffset2)
            # self.readImageStrips(ifd1)

    def readIFDFromOffset(self, tags, offset):
        # Read first IFD
        self.rf.seek(offset)
        (numFields,) = struct.unpack('H', self.rf.read(2))
        for i in range(0, numFields):
            tag = TAG()
            tag.tell = self.rf.tell()
            (tag.tag,) = struct.unpack('H', self.rf.read(2))
            (tag.type,) = struct.unpack('H', self.rf.read(2))
            (tag.count,) = struct.unpack('I', self.rf.read(4))
            if tag.type == 1 and tag.count <= 4:
                for j in range(0, 4):
                    (value,) = struct.unpack('B', self.rf.read(1))
                    tag.value.append(value)
            elif tag.type == 3 and tag.count <= 2:
                for j in range(0, 2):
                    (value,) = struct.unpack('H', self.rf.read(2))
                    tag.value.append(value)
            elif tag.type == 4 and tag.count == 1:
                (value,) = struct.unpack('I', self.rf.read(4))
                tag.value.append(value)
            elif tag.type == 6 and tag.count <= 4:
                for j in range(0, 4):
                    (value,) = struct.unpack('b', self.rf.read(1))
                    tag.value.append(value)
            elif tag.type == 7 and tag.count <= 4:
                for j in range(0, 4):
                    (value,) = struct.unpack('b', self.rf.read(1))
                    tag.value.append(value)
            elif tag.type == 8 and tag.count <= 2:
                for j in range(0, 2):
                    (value,) = struct.unpack('h', self.rf.read(2))
                    tag.value.append(value)
            elif tag.type == 9 and tag.count == 1:
                (value,) = struct.unpack('i', self.rf.read(4))
                tag.value.append(value)
            elif tag.type == 11 and tag.count == 1:
                (value,) = struct.unpack('f', self.rf.read(4))
                tag.value.append(value)
            else:
                (tag.offset,) = struct.unpack('I', self.rf.read(4))
            if tag.offset != 0:
                tag.readValue(self.rf)
            tags[tag.tag] = tag

    def writeImageStrips(self, ifd):
        try:
            stripOffsetsTag = ifd.tags[DNG_TAGS_STR_ID['StripOffsets']]
        except KeyError:
            return
        rowsPerStrip = ifd.tags[DNG_TAGS_STR_ID['RowsPerStrip']].value[0]
        numStrips = ifd.imageHeight / rowsPerStrip
        stripOffsetsTag = ifd.tags[DNG_TAGS_STR_ID['StripOffsets']]
        stripOffsets = []
        beginTell = self.wf.tell()

        stripOffsets.append(self.wf.tell())

        data = ifd.image
        data.dtype = np.uint16
        out = np.zeros((data.shape[0], int(data.shape[1]*1.25)), dtype=np.uint8)

        out[:,::5] = data[:,::4] >> 2
        out[:,1::5] = ((data[:,::4] & 0b0000000000000011 ) << 6)
        out[:,1::5] += data[:,1::4] >> 4
        out[:,2::5] = ((data[:,1::4] & 0b0000000000001111 ) << 4)
        out[:,2::5] += data[:,2::4] >> 6
        out[:,3::5] = ((data[:,2::4] & 0b0000000000111111 ) << 2)
        out[:,3::5] += data[:,3::4] >> 8
        out[:,4::5] = data[:,3::4] & 0b0000000011111111 

        self.wf.write(out.tobytes())

        currentTell = self.wf.tell()

        self.wf.seek(stripOffsetsTag.offset)
        if (stripOffsetsTag.count == 1):
            self.wf.write(struct.pack('I', stripOffsets[0]))
        else:
            for offset in stripOffsets:
                self.wf.write(struct.pack('I', offset))
        self.wf.seek(currentTell)

    def printIDFs(self):
        ordered = collections.OrderedDict(sorted(self.ifd.tags.items()))
        for key, tag in ordered.iteritems():
            tag.printTAG()

    def closeDNG(self):
        self.rf.close()
        self.wf.close()


for key, tag in DNG_TAGS_STR_ID.items():
    DNG_TAGS_ID_STR[tag] = key