# from distutils.core import setup, Extension
from setuptools import setup, Extension
import setuptools
import os
import shutil
import platform


ljpeg92 = Extension('ljpegCompress', sources = ["pydng/bitunpack.c", "pydng/liblj92/lj92.c"],  extra_compile_args=['-std=gnu99'], extra_link_args=[])

setup ( 
    name = "pydng", 
    version = "3.4.1", 
    author="Csaba Nagy",
    description = "Python utility for converting Raspberry Pi Camera RAW images into Adobe DNG Format.", 
    url="https://github.com/schoolpost/PyDNG",
    packages=['pydng'],
    install_requires=[
          'numpy',
          'exifread',
      ],
    ext_modules = [ljpeg92],
    python_requires='>=3.5',
    )


