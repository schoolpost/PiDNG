PYDNG V3.4.0
=========

Create Adobe DNG RAW files using Python3. Developed primilariy for use with Raspberry Pi Camera Modules. ( JPEG+RAW Mode )

![](demo.jpg)

### Works with:
- OV5467 ( Raspberry Pi Camera Module V1 )
- IMX219 ( Raspberry Pi Camera Module V2 )
- IMX477( Raspberry Pi High Quality Camera )

Instructions
------------

Requires: 
- Python3 
- Numpy  
- ExifRead



```
#install 
pip install src/.

#examples
Usage:
  from pydng.core import RPICAM2DNG

  d = RPICAM2DNG()

  # example using a stream
  output = d.convert(stream)

  # example using a file string input
  d.convert('color.jpg')


Utility.py:
  python examples/utility.py <options> <inputFilename> 
  python examples/utility.py color.jpg  

```

TODO
------------

-Apply calibrated color matrix values 


Credits
------------
Source referenced from:

Waveform80 | [picamera](https://github.com/waveform80/picamera)

Krontech | [chronos-utils](https://github.com/krontech/chronos-utils)

Andrew Baldwin | [MLVRawViewer](https://bitbucket.org/baldand/mlrawviewer)


