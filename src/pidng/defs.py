# Read more about tags and their definitions/values here:
# https://exiftool.org/TagNames/EXIF.html
# https://www.adobe.com/content/dam/acom/en/products/photoshop/pdfs/dng_spec_1.4.0.0.pdf


class Compression:
    Uncompressed = 1
    LJ92 = 7 #Lossless JPEG
    Lossy_JPEG = 34892

class PreviewColorSpace:
    Unknown = 0
    Gray_Gamma_22 = 1
    sRGB = 2
    Adobe_RGB = 3
    ProPhoto_RGB = 4

class Orientation:
    Horizontal = 1
    MirrorH = 2
    Rotate180 = 3
    MirrorV = 4

class DNGVersion:
    V1_0 = [1, 0, 0, 0]
    V1_1 = [1, 1, 0, 0]
    V1_2 = [1, 2, 0, 0]
    V1_3 = [1, 3, 0, 0]
    V1_4 = [1, 4, 0, 0]
    V1_5 = [1, 5, 0, 0]
    V1_6 = [1, 6, 0, 0]

class PhotometricInterpretation:
    WhiteIsZero = 0
    BlackIsZero = 1
    RGB = 2
    Linear_Raw = 34892 
    Color_Filter_Array = 32803 

class CFAPattern:
    BGGR = [2, 1, 1, 0]
    GBRG = [1, 2, 0, 1]
    GRBG = [1, 0, 2, 1]
    RGGB = [0, 1, 1, 2]

class CalibrationIlluminant:   
    Unknown = 0
    Daylight = 1
    Fluorescent = 2
    Tungsten_Incandescent = 3
    Flash = 4
    Fine_Weather = 9
    Cloudy = 10
    Shade = 11
    Daylight_Fluorescent = 12
    Day_White_Fluorescent = 13
    Cool_White_Fluorescent = 14
    White_Fluorescent = 15
    Warm_White_Fluorescent = 16 
    Standard_Light_A = 17
    Standard_Light_B = 18
    Standard_Light_C = 19
    D55 = 20
    D65 = 21
    D75 = 22
    D50 = 23
    ISO_Studio_Tungsten = 24
    Other = 255