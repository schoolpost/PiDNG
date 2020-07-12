PYDNG
=========
![](https://img.shields.io/badge/Version-3.4.1-green.svg)

Create Adobe DNG RAW files using Python.

![](demo.jpg)

**Features**
------------

- 8,10,12,14,16-bit precision
- Lossless compression
- DNG Tags ( extensible )

### Works with any **Bayer RAW** Data including native support for **Raspberry Pi cameras**.
- OV5467 ( Raspberry Pi Camera Module V1 )
- IMX219 ( Raspberry Pi Camera Module V2 )
- IMX477( Raspberry Pi High Quality Camera )

*Raspberry Pi High Quality Camera examples below ( DNG top, JPEG bottom )*

![](collage.jpg)

***

Instructions
------------

Requires: 
- Python3 
- Numpy  
- ExifRead


### Install

```
# download
git clone https://github.com/schoolpost/PyDNG.git
cd PyDNG

# install 
pip3 install src/.

# or
pip install src/.

```
### How to use:

```

# examples
from pydng.core import RPICAM2DNG

# use file string input to the jpeg+raw file. 
d = RPICAM2DNG()
d.convert('imx477.jpg')


# the included command line utility can be used as shown below
Utility.py:
  python3 examples/utility.py <options> <inputFilename> 
  python3 examples/utility.py imx477.jpg  

```

***

TODO
------------

- SUB IFDS/THUMBNAILS

***

Credits
------------
Source referenced from:

CanPi ( Jack ) | [color-matrices](https://www.raspberrypi.org/forums/viewtopic.php?f=43&t=278828)

Waveform80 | [picamera](https://github.com/waveform80/picamera)

Krontech | [chronos-utils](https://github.com/krontech/chronos-utils)

Andrew Baldwin | [MLVRawViewer](https://bitbucket.org/baldand/mlrawviewer)


