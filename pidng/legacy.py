
import ctypes

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

BAYER_ORDER = {
    0: [0, 1, 1, 2],
    1: [1, 2, 0, 1],
    2: [2, 1, 1, 0],
    3: [1, 0, 2, 1],
}
