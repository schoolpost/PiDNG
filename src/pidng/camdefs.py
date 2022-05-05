import json
import re
import numpy as np
from .dng import DNGTags, Tag
from .defs import *


class RaspberryPiCameraModels:
    Raspberry_Pi_Camera_V1 = "Raspberry Pi Camera V1"
    Raspberry_Pi_Camera_V2 = "Raspberry Pi Camera V2"
    Raspberry_Pi_High_Quality_Camera = "Raspberry Pi High Quality Camera"


class BaseCameraModel():
    def __init__(self) -> None:
        self.tags = DNGTags()
        self.model = "BaseCameraModel"

    def __settings__(self) -> None:
        pass

    # TODO
    def fromDict(dict : dict) -> None:  
        pass

    # TODO
    def fromJson(jsn : str) -> None:
        parameters = json.loads(jsn)

    def __repr__(self) -> DNGTags:
        return self.tags

    def __str__(self) -> str:
        return str(self.model)

class Picamera2Camera(BaseCameraModel):
    def __init__(self, fmt : dict, metadata: dict) -> None:
        super().__init__() 
        self.model = "Picamera2Model"
        self.fmt = fmt
        self.metadata = metadata
        self.__settings__()

    def __settings__(self) -> None:

        width, height = self.fmt.get("size", (0,0))
        fmt_str = self.fmt.get("format","").split("_")[0]
        bpp = int(re.search(r'\d+', fmt_str).group())
        self.fmt["bpp"] = bpp

        black_levels = list()
        for val in self.metadata.get("SensorBlackLevels", (0)):
            black_levels.append((val >> (16 - bpp)))
        
        camera_calibration = [[1, 1], [0, 1], [0, 1],
                              [0, 1], [1, 1], [0, 1],
                              [0, 1], [0, 1], [1, 1]]

        color_gain_div = 10000
        gain_r, gain_b = self.metadata.get("ColourGains",(color_gain_div, color_gain_div))
        gain_matrix = np.array([[gain_r, 0, 0],
                                [0, 1.0, 0],
                                [0, 0, gain_b]])
        gain_r = int(gain_r * color_gain_div)
        gain_b = int(gain_b * color_gain_div)
        as_shot_neutral = [[color_gain_div, gain_r], [color_gain_div, color_gain_div], [color_gain_div, gain_b]]

        ccm1 = list()
        ccm = self.metadata["ColourCorrectionMatrix"]
	# This maxtrix from http://www.brucelindbloom.com/index.html?Eqn_RGB_XYZ_Matrix.html
        rgb_to_xyz = np.array([[0.4124564, 0.3575761, 0.1804375],
		               [0.2126729, 0.7151522, 0.0721750],
		               [0.0193339, 0.1191920, 0.9503041]])
        ccm_matrix = np.array(ccm).reshape((3, 3))
        ccm = np.linalg.inv(rgb_to_xyz.dot(ccm_matrix).dot(gain_matrix))

        for color in ccm.flatten().tolist():
            ccm1.append((int(color*color_gain_div), color_gain_div))

        ci1 = CalibrationIlluminant.D65

        baseline_exp = 1

        model = "PiDNG / PiCamera2"
        make = "RaspberryPi"

        profile_name = "PiDNG / PiCamera2 Profile"
        profile_embed = 3

        self.orientation = 1
        if "BGGR" in fmt_str:
            self.cfaPattern = CFAPattern.BGGR
        elif "GBRG" in fmt_str:
            self.cfaPattern = CFAPattern.GBRG
        elif "GRBG" in fmt_str:
            self.cfaPattern = CFAPattern.GRBG
        elif "RGGB" in fmt_str:
            self.cfaPattern = CFAPattern.RGGB

        exposure_time = int(1/(self.metadata["ExposureTime"] * 0.000001))
        total_gain = self.metadata["AnalogueGain"] * self.metadata["DigitalGain"]
        iso = int(total_gain * 100)

        self.tags.set(Tag.PhotographicSensitivity, [iso]) 
        self.tags.set(Tag.ExposureTime, [[1,exposure_time]])  
        self.tags.set(Tag.RawDataUniqueID, str(self.metadata["SensorTimestamp"]).encode("ascii"))
        self.tags.set(Tag.ImageWidth, width)
        self.tags.set(Tag.ImageLength, height)
        self.tags.set(Tag.TileWidth, width)
        self.tags.set(Tag.TileLength, height)
        self.tags.set(Tag.Orientation, self.orientation)
        self.tags.set(Tag.PhotometricInterpretation, PhotometricInterpretation.Color_Filter_Array)
        self.tags.set(Tag.SamplesPerPixel, 1)
        self.tags.set(Tag.BitsPerSample, bpp)
        self.tags.set(Tag.CFARepeatPatternDim, [2,2])
        self.tags.set(Tag.CFAPattern, self.cfaPattern)
        self.tags.set(Tag.BlackLevelRepeatDim, [2,2])
        self.tags.set(Tag.BlackLevel, black_levels)
        self.tags.set(Tag.WhiteLevel, ((1 << bpp) -1) )
        self.tags.set(Tag.ColorMatrix1, ccm1)
        self.tags.set(Tag.CameraCalibration1, camera_calibration)
        self.tags.set(Tag.CameraCalibration2, camera_calibration)
        self.tags.set(Tag.CalibrationIlluminant1, ci1)
        self.tags.set(Tag.BaselineExposure, [[baseline_exp,1]])
        self.tags.set(Tag.AsShotNeutral, as_shot_neutral)
        self.tags.set(Tag.Make, make)
        self.tags.set(Tag.Model, model)
        self.tags.set(Tag.ProfileName, profile_name)
        self.tags.set(Tag.ProfileEmbedPolicy, [profile_embed])
        
class RaspberryPiHqCamera(BaseCameraModel):
    def __init__(self, sensor_mode : int, cfaPattern=CFAPattern.BGGR, orientation=Orientation.Horizontal) -> None:
        super().__init__()
        self.model = RaspberryPiCameraModels.Raspberry_Pi_High_Quality_Camera
        self.mode = sensor_mode
        self.orientation = orientation
        self.cfaPattern = cfaPattern
        self.__settings__()

    def __settings__(self) -> None:
        width = None
        height = None
        bpp = None

        if self.mode == 1:
            width = 2028
            height = 1080
        if self.mode == 2:
            width = 2028
            height = 1520
        if self.mode == 3:
            width = 4056
            height = 3040
        if self.mode == 4:
            width = 1012
            height = 760

        if self.mode < 4:
            bpp = 12
        else: 
            bpp = 10

        profile_name = "Repro 2_5D no LUT - D65 is really 5960K"
        profile_embed = 3

        ccm1 = [[6759, 10000], [-2379, 10000], [751, 10000],
                [-4432, 10000], [13871, 10000], [5465, 10000],
                [-401, 10000], [1664, 10000], [7845, 10000]]

        ccm2 = [[5603, 10000], [-1351, 10000], [-600, 10000],
                [-2872, 10000], [11180, 10000], [2132, 10000],
                [600, 10000], [453, 10000], [5821, 10000]]

        fm1 = [[7889, 10000], [1273, 10000], [482, 10000],
                [2401, 10000], [9705, 10000], [-2106, 10000],
                [-26, 10000], [-4406, 10000], [12683, 10000]]

        fm2 = [[6591, 10000], [3034, 10000], [18, 10000],
                [1991, 10000], [10585, 10000], [-2575, 10000],
                [-493, 10000], [-919, 10000], [9663, 10000]]

        camera_calibration = [[1, 1], [0, 1], [0, 1],
                              [0, 1], [1, 1], [0, 1],
                              [0, 1], [0, 1], [1, 1]]

        gain_r = 2500
        gain_b = 2000

        as_shot_neutral = [[1000, gain_r], [1000, 1000], [1000, gain_b]]

        ci1 = CalibrationIlluminant.Standard_Light_A
        ci2 = CalibrationIlluminant.D65

        model = " ".join(self.model.split(" ")[2:])
        make = " ".join(self.model.split(" ")[:-3])

        baseline_exp = 1

        self.tags.set(Tag.ImageWidth, width)
        self.tags.set(Tag.ImageLength, height)
        self.tags.set(Tag.TileWidth, width)
        self.tags.set(Tag.TileLength, height)
        self.tags.set(Tag.Orientation, self.orientation)
        self.tags.set(Tag.PhotometricInterpretation, PhotometricInterpretation.Color_Filter_Array)
        self.tags.set(Tag.SamplesPerPixel, 1)
        self.tags.set(Tag.BitsPerSample, bpp)
        self.tags.set(Tag.CFARepeatPatternDim, [2,2])
        self.tags.set(Tag.CFAPattern, self.cfaPattern)
        self.tags.set(Tag.BlackLevel, (4096 >> (16 - bpp)))
        self.tags.set(Tag.WhiteLevel, ((1 << bpp) -1) )
        self.tags.set(Tag.ColorMatrix1, ccm1)
        self.tags.set(Tag.ColorMatrix2, ccm2)
        self.tags.set(Tag.ForwardMatrix1, fm1)
        self.tags.set(Tag.ForwardMatrix2, fm2)
        self.tags.set(Tag.CameraCalibration1, camera_calibration)
        self.tags.set(Tag.CameraCalibration2, camera_calibration)
        self.tags.set(Tag.CalibrationIlluminant1, ci1)
        self.tags.set(Tag.CalibrationIlluminant2, ci2)
        self.tags.set(Tag.BaselineExposure, [[baseline_exp,1]])
        self.tags.set(Tag.AsShotNeutral, as_shot_neutral)
        self.tags.set(Tag.Make, make)
        self.tags.set(Tag.Model, model)
        self.tags.set(Tag.ProfileName, profile_name)
        self.tags.set(Tag.ProfileEmbedPolicy, [profile_embed])


# TODO
class RaspberryPiCameraV2(BaseCameraModel):
    pass



# TODO
class RaspberryPiCameraV1(BaseCameraModel):
    pass
