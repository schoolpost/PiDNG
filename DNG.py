import struct, collections
import numpy as np
from DNGTags import *

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
        #print "Endian: ", self.endian
        (self.magicNum,) = struct.unpack('h',self.rf.read(2))
        if self.magicNum != 42:
            quit()
        #print "Successfully read header."
    def writeHeader(self):
        self.wf.write(struct.pack('2s',self.endian))
        self.wf.write(struct.pack('H',self.magicNum))
        self.wf.write(struct.pack('I',8))
    def writeIFD(self,ifd):
        self.wf.write(struct.pack('H',len(ifd.tags)))
        sortedTags = sorted(ifd.tags.iterkeys())
        tagsToWriteOffset = []
        
        try:
            subIFDTag = ifd.tags[DNG_TAGS_STR_ID['SubIFDs']]
            subIFDTag.count = len(ifd.subIFDs)
        except KeyError:
            pass
        
        for key in sortedTags:
            tag = ifd.tags[key]
            self.wf.write(struct.pack('H',tag.tag))
            self.wf.write(struct.pack('H',tag.type))
            self.wf.write(struct.pack('I',tag.count))
            tag.offset = self.wf.tell()
            if tag.type == 1 and tag.count <= 4:
                for j in range(0,4):
                    self.wf.write(struct.pack('B',tag.value[j]))
            elif tag.type == 3 and tag.count <= 2:
                for j in range(0,2):
                    self.wf.write(struct.pack('H',tag.value[j]))           
            elif tag.type == 4 and tag.count == 1:
                    self.wf.write(struct.pack('I',tag.value[0])) 
            elif tag.type == 6 and tag.count <= 4:
                for j in range(0,4):
                    self.wf.write(struct.pack('b',tag.value[j]))
            elif tag.type == 7 and tag.count <= 4:
                for j in range(0,4):
                    self.wf.write(struct.pack('b',tag.value[j]))
            elif tag.type == 8 and tag.count <= 2:
                for j in range(0,2):
                    self.wf.write(struct.pack('h',tag.value[j]))
            elif tag.type == 9 and tag.count == 1:
                    self.wf.write(struct.pack('i',tag.value[0]))
            elif tag.type == 11 and tag.count == 1:
                    self.wf.write(struct.pack('f',tag.value[0]))
            else:
                #tag.offset = self.wf.tell()
                tagsToWriteOffset.append(tag)
                self.wf.write(struct.pack('I',tag.offset))
        #Last IFD tag
        self.wf.write(struct.pack('I',0))
        for tag in tagsToWriteOffset:
            tag.writeTAG(self.wf)
        if( hasattr(ifd,'image') ):
            self.writeImageStrips(ifd)
        try:
            subIFDTag = ifd.tags[DNG_TAGS_STR_ID['SubIFDs']]
            subTagNum = 0
            for subIFD in ifd.subIFDs:
                preTell = self.wf.tell()
                self.writeIFD(subIFD)
                currentTell = self.wf.tell()
                self.wf.seek(subIFDTag.offset + 4*subTagNum)
                self.wf.write(struct.pack('I',preTell))
                self.wf.seek(currentTell)
                subTagNum += 1
        except KeyError:
            pass
    def readIFDs(self):
        (self.ifd.offset,) = struct.unpack('I',self.rf.read(4))
        self.readIFDFromOffset(self.ifd.tags, self.ifd.offset)
        try:
            if self.ifd.getTag('StripByteCounts').count > 0:
                self.readImageStrips(self.ifd)
        except KeyError:
            pass
    def readSubIFD(self,strTag):
        try:
            tag = self.ifd.tags[DNG_TAGS_STR_ID[strTag]]
        except KeyError:
            return
        
        if tag.count == 1:
            ifd1 = IFD()
            ifd1.offset = tag.value[0]
            self.ifd.subIFDs.append(ifd1)
            self.readIFDFromOffset(ifd1.tags, tag.value[0])
            self.readImageStrips(ifd1)
        else:
            # Multiple Sub IFDs
            # TODO: Add support for any number of Sub IFDs and make recursive
            self.rf.seek(tag.offset)
            (subIFDOffset1,) = struct.unpack('I',self.rf.read(4))
            (subIFDOffset2,) = struct.unpack('I',self.rf.read(4))
            
            ifd1 = IFD()
            ifd1.offset = subIFDOffset1
            ifd2 = IFD()
            ifd2.offset = subIFDOffset2
            self.ifd.subIFDs.append(ifd1)
            self.ifd.subIFDs.append(ifd2)
            
            self.readIFDFromOffset(ifd1.tags, subIFDOffset1)
            self.readIFDFromOffset(ifd2.tags, subIFDOffset2)
            self.readImageStrips(ifd1)
    def readIFDFromOffset(self, tags, offset):
        # Read first IFD
        self.rf.seek(offset)
        (numFields,) = struct.unpack('H',self.rf.read(2))
        for i in range(0,numFields):
            tag = TAG()
            tag.tell = self.rf.tell()
            (tag.tag,) = struct.unpack('H',self.rf.read(2))
            (tag.type,) = struct.unpack('H',self.rf.read(2))
            (tag.count,) = struct.unpack('I',self.rf.read(4))
            if tag.type == 1 and tag.count <= 4:
                for j in range(0,4):
                    (value,) = struct.unpack('B',self.rf.read(1))
                    tag.value.append(value)
            elif tag.type == 3 and tag.count <= 2:
                for j in range(0,2):
                    (value,) = struct.unpack('H',self.rf.read(2))
                    tag.value.append(value)            
            elif tag.type == 4 and tag.count == 1:
                    (value,) = struct.unpack('I',self.rf.read(4))
                    tag.value.append(value)  
            elif tag.type == 6 and tag.count <= 4:
                for j in range(0,4):
                    (value,) = struct.unpack('b',self.rf.read(1))
                    tag.value.append(value)   
            elif tag.type == 7 and tag.count <= 4:
                for j in range(0,4):
                    (value,) = struct.unpack('b',self.rf.read(1))
                    tag.value.append(value)  
            elif tag.type == 8 and tag.count <= 2:
                for j in range(0,2):
                    (value,) = struct.unpack('h',self.rf.read(2))
                    tag.value.append(value)
            elif tag.type == 9 and tag.count == 1:
                    (value,) = struct.unpack('i',self.rf.read(4))
                    tag.value.append(value)
            elif tag.type == 11 and tag.count == 1:
                    (value,) = struct.unpack('f',self.rf.read(4))
                    tag.value.append(value)
            else:
                (tag.offset,) = struct.unpack('I',self.rf.read(4))
            if tag.offset != 0:
                tag.readValue(self.rf)
            tags[tag.tag] = tag
            
    '''
    TODO: don't refer to raw image ifd, refer to current ifd   
    Processes tiles instead of strips         
    def readImageTiles(self, ifd):
        
        ifd.imageWidth = dng.ifd.subIFDs[0].tags[DNG_TAGS_STR_ID['ImageWidth']].offset
        ifd.imageHeight = dng.ifd.subIFDs[0].tags[DNG_TAGS_STR_ID['ImageLength']].offset
        tileWidth = dng.ifd.subIFDs[0].tags[DNG_TAGS_STR_ID['TileWidth']].offset
        tileLength = dng.ifd.subIFDs[0].tags[DNG_TAGS_STR_ID['TileLength']].offset
        firstTileOffset = dng.ifd.subIFDs[0].tags[DNG_TAGS_STR_ID['TileOffsets']].offset
        numTiles = dng.ifd.subIFDs[0].tags[DNG_TAGS_STR_ID['TileOffsets']].count
        numTilesWide = int(round((ifd.imageWidth+0.0)/tileWidth))
        numTilesLong = int(round((ifd.imageHeight+0.0)/tileLength))
        self.image = np.zeros((ifd.imageHeight,ifd.imageWidth),dtype=np.uint8)
        self.rf.seek(firstTileOffset)
        offsets = []
        tileByteCounts = []
        
        for i in range(0, numTiles):
            (tileOffset,) = struct.unpack('I',self.rf.read(4))
            offsets.append(tileOffset)
            
        self.rf.seek(dng.ifd.subIFDs[0].tags[DNG_TAGS_STR_ID['TileByteCounts']].offset)
        for i in range(0, numTiles):
            (byteCount,) = struct.unpack('I',self.rf.read(4))
            tileByteCounts.append(byteCount)
            
        tileCount = 0
        
        for tileYCount in range(0,numTilesLong):
            for tileXCount in range(0,numTilesWide):
                self.rf.seek(offsets[tileCount])
                tileCount = tileCount + 1
                
                for y in range(0,tileLength):
                    for x in range(0,tileWidth):
                        pixelX = tileXCount*tileWidth+x
                        pixelY = tileYCount*tileLength+y
                        if pixelX < ifd.imageWidth and pixelY < ifd.imageHeight:
                            (data,) = struct.unpack('H',self.rf.read(2))
                            ifd.image[pixelY,pixelX] = (data+1.0)/2**16*255-1
    '''

    def readImageStrips(self, ifd):
        ifd.imageWidth = ifd.tags[DNG_TAGS_STR_ID['ImageWidth']].value[0]
        ifd.imageHeight = ifd.tags[DNG_TAGS_STR_ID['ImageLength']].value[0]
        rowsPerStrip = ifd.tags[DNG_TAGS_STR_ID['RowsPerStrip']].value[0]
        stripOffsets = ifd.tags[DNG_TAGS_STR_ID['StripOffsets']].value
        
        ifd.image = np.zeros((ifd.imageHeight,ifd.imageWidth),dtype=np.uint16)
        numStrips = ifd.imageHeight/rowsPerStrip

        for stripNum in range(0,numStrips):
            self.rf.seek(stripOffsets[stripNum])
            for rowNum in range(0,rowsPerStrip):
                rowData = struct.unpack(str(ifd.imageWidth)+'H',self.rf.read(2*ifd.imageWidth))
                ifd.image[stripNum*rowsPerStrip+rowNum,:] = rowData

    def writeImageStrips(self,ifd):
        try:
            stripOffsetsTag = ifd.tags[DNG_TAGS_STR_ID['StripOffsets']]
        except KeyError:
            return
        rowsPerStrip = ifd.tags[DNG_TAGS_STR_ID['RowsPerStrip']].value[0]
        numStrips = ifd.imageHeight/rowsPerStrip
        stripOffsetsTag = ifd.tags[DNG_TAGS_STR_ID['StripOffsets']]
        stripOffsets = []
        beginTell = self.wf.tell()
        for stripNum in range(0,numStrips):
            stripOffsets.append(self.wf.tell())
            for rowNum in range(0,rowsPerStrip):
                rowData = ifd.image[stripNum*rowsPerStrip+rowNum,:]
                self.wf.write(struct.pack('H'*len(rowData),*rowData))
                
        currentTell = self.wf.tell()
        
        self.wf.seek(stripOffsetsTag.offset)
        if(stripOffsetsTag.count == 1 ):          
            self.wf.write(struct.pack('I',stripOffsets[0]))
        else:
            for offset in stripOffsets:
                self.wf.write(struct.pack('I',offset))
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
