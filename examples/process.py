from pidng.core import RPICAM2DNG


def processing(raw, _dummy):
    # access to the bayer raw numpy array here. 
    print(raw.shape, raw.size)
    return raw

RPICAM2DNG().convert("../imx477.jpg", process=processing)