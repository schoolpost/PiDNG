# generate 10-bit DNG from PiCamera V2 ( Sony IMX219 )
from DNG_10 import *
import io
import os


def createDNG(input_file):
    def addTag(dict, ifd, tagName):
        dict[DNG_TAGS_STR_ID[tagName]] = ifd.getTag(tagName)

    def delTag(ifd, tagName):
        del ifd.tags[DNG_TAGS_STR_ID[tagName]]

    organization = "NameHere"
    cameraModel = "NameHere"
    emptyDNG = 'empty.dng'
    outputDNG = input_file.strip('.jpg') + '.dng'

    dng = DNG(emptyDNG)
    dng.openDNG()
    dng.readHeader()
    dng.readIFDs()
    dng.readSubIFD('SubIFDs')

    makeTag = dng.ifd.getTag('Make')
    makeTag.value = organization
    makeTag.count = len(makeTag.value)
    modelTag = dng.ifd.getTag('Model')
    modelTag.value = organization + " " + cameraModel
    modelTag.count = len(modelTag.value)
    uniqueCameraModelTag = dng.ifd.getTag('UniqueCameraModel')
    uniqueCameraModelTag.value = modelTag.value
    uniqueCameraModelTag.count = modelTag.count
    origRawFileNameTag = dng.ifd.getTag('OriginalRawFileName')
    origRawFileNameTag.value = emptyDNG
    origRawFileNameTag.count = len(origRawFileNameTag.value)

    camCalTag = dng.ifd.getTag('CameraCalibrationSignature')
    camCalTag.value = organization
    camCalTag.count = len(camCalTag.value)
    profCalTag = dng.ifd.getTag('ProfileCalibrationSignature')
    profCalTag.value = organization
    profCalTag.count = len(profCalTag.value)

    # Camera calibration
    matrix1Tag = dng.ifd.getTag('ColorMatrix1')
    matrix1Tag.value[0].num = 19549
    matrix1Tag.value[1].num = -7877
    matrix1Tag.value[2].num = -2582
    matrix1Tag.value[3].num = -5724
    matrix1Tag.value[4].num = 10121
    matrix1Tag.value[5].num = 1917
    matrix1Tag.value[6].num = -1267
    matrix1Tag.value[7].num = -110
    matrix1Tag.value[8].num = 6621

    for i in range(0, 9):
        matrix1Tag.value[i].denom = 100

    delTag(dng.ifd, 'ColorMatrix2')
    calIllum1Tag = dng.ifd.getTag('CalibrationIlluminant1')
    calIllum1Tag.value[0] = 1
    delTag(dng.ifd, 'CalibrationIlluminant2')
    delTag(dng.ifd, 'CameraCalibration1')
    delTag(dng.ifd, 'CameraCalibration2')

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

    def hotPixelRemove(img, ref):
        ref_txt = open(ref, 'r+')
        pxl_lines = ref_txt.read().splitlines()
        pxl_data = []
        for i in pxl_lines:
            x = i.split(' ')
            pxl_data.append(x[:2])

        for k in pxl_data:
            k0 = int(k[0])
            k1 = int(k[1])
            array = list()
            for i in range(-1, 2):
                for j in range(-1, 2):
                    if i != 0 or j != 0:
                        try:
                            array.append(img[k1 + i][k0 + j])
                        except IndexError:
                            pass
            img[k1][k0] = np.median(array)

    # extract bayer raw to 16bit numyp array
    rawImage = extractRAW(input_file)

    # raw image white and black levels
    black_level = rawImage.min()
    white_level = rawImage.max()

    # lens shade frame
    shading_median = np.fromfile('shade/shade_sun', dtype=np.uint16)
    shading_median = np.reshape(shading_median, rawImage.shape)

    # dark frame
    black_levels = np.mean(np.fromfile('dark/dark_frame', dtype=np.uint16))
    black_median = np.ones(rawImage.shape) * black_levels

    # flat-field correction
    output = ((rawImage - black_median) * np.mean(shading_median - black_median) / (shading_median - black_median))

    # remove hot pixels with pixel location txt file.
    hotPixelRemove(output, 'pxl.txt')

    # map values back to orignal range
    rawImage = np.interp(output, [output.min(), output.max()], [black_level, white_level])

    # convert to 16bit array
    rawImage = np.uint16(rawImage)

    # bayer matrix tags
    width = rawImage.shape[1]
    height = rawImage.shape[0]
    rawIFD = dng.ifd.subIFDs[0]
    rawIFD.image = rawImage
    rawIFD.imageWidth = width
    rawIFD.imageHeight = height
    rawIFD.getTag('ImageWidth').value[0] = width
    rawIFD.getTag('ImageLength').value[0] = height
    rawIFD.getTag('StripByteCounts').value[0] = width * height * 2
    rawIFD.getTag('BitsPerSample').value[0] = 10
    rawIFD.getTag('SamplesPerPixel').value[0] = 1
    rawIFD.getTag('RowsPerStrip').value[0] = height
    rawIFD.getTag('ActiveArea').value[0] = 0
    rawIFD.getTag('ActiveArea').value[1] = 0
    rawIFD.getTag('ActiveArea').value[2] = height
    rawIFD.getTag('ActiveArea').value[3] = width
    rawIFD.getTag('DefaultCropSize').value[0].num = width
    rawIFD.getTag('DefaultCropSize').value[1].num = height
    rawIFD.getTag('DefaultCropOrigin').value[0].num = 0
    rawIFD.getTag('DefaultCropOrigin').value[1].num = 0

    # set white and black levels
    new_blck = RATIONAL()
    new_blck.num = black_level
    rawIFD.getTag('BlackLevel').value[0] = new_blck
    rawIFD.getTag('WhiteLevel').value[0] = 1023

    # Change Order to GBRG when y-flipped
    rawIFD.getTag('CFAPattern').value[0] = 2
    rawIFD.getTag('CFAPattern').value[1] = 1
    rawIFD.getTag('CFAPattern').value[2] = 1
    rawIFD.getTag('CFAPattern').value[3] = 0

    dng.writeDNG(outputDNG)
    print(input_file + ' converted to ' + outputDNG)


createDNG('color.jpg')
