# PyDNG
Python based Adobe DNG RAW Converter. Tuned for use with the Raspberry Pi Camera. 

Requires: Python2.7 and Numpy

Convert raw bayer data from raw containing .jpgs from the Raspberry Pi Camera V2 ( SonyIMX219 )

Calibration and Bayer Matrix corrections are included in the dark/shade/pxl folders.

dark - Contains 16-bit bayer dark images in numpy format.  

shade - Contains 16-bit bayer lens shading profiles in numpy format. 

pxl - Contains a .txt with list of pixel locations with hot/dead pixels. ( first 2 values. x,y locations. ignore 3rd. ) 

Note: You can use the provided references, but users should generate calibration from their own unqiue sensors as variations likely exist for best results. 

pydng.py - Main python file used for generating the DNG. Pass input file string into function, change appropraite tags if desired ( model, make, organization ) 

Output is 10bit DNG file

Usage Exmaple: pydng.createDNG('color.jpg')

Raspberry Pi Camera V1 ( OV5647 ) is untested.

# TODO List:

-Copy EXIF Data from .jpg to .dng

-Fix magenta tinted highlights

-Apply calibrated color matrix values 

-Automated calibration script to let users generate dark/shade/pxl from input images

# License

This project is licensed under the terms of the [MIT license](https://opensource.org/licenses/MIT).
