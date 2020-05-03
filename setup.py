# from distutils.core import setup, Extension
from setuptools import setup, Extension
import setuptools
import os
import shutil
import platform


ljpeg92 = Extension('ljpegCompress', sources = ["bitunpack.c", "liblj92/lj92.c"],  extra_compile_args=['-std=gnu99'], extra_link_args=[])

setup ( 
    name = "PyDNG", 
    version = "3.0", 
    author="Csaba Nagy",
    description = "Python utility for converting Raspberry Pi Camera RAW images into Adobe DNG Formayt.", 
    url="https://github.com/schoolpost/PyDNG",
    packages=setuptools.find_packages(),
    ext_modules = [ljpeg92],
    python_requires='>=3.6',
    )

dirName = 'build/'
listOfFiles = list()
for (dirpath, dirnames, filenames) in os.walk(dirName):
    for file in filenames:
        if file.endswith('.so'):
            shutil.move(os.path.join(dirpath, file), '.')

shutil.rmtree('build/')


