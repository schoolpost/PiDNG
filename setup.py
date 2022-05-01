# from distutils.core import setup, Extension
from setuptools import setup, Extension

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

ljpeg92 = Extension('ljpegCompress', sources=[
                    "src/pidng/bitunpack.c", "src/pidng/liblj92/lj92.c"],  extra_compile_args=['-std=gnu99'], extra_link_args=[])

setup(
    name="pidng",
    version="4.0.0",
    author="Csaba Nagy",
    description="Python utility for creating Adobe DNG files from RAW image data.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/schoolpost/PiDNG",
    packages=['pidng'],
    install_requires=[
        'numpy',
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    ext_modules=[ljpeg92],
    package_dir={"": "src"},
    python_requires='>=3.6',
)
