from distutils.core import setup, Extension
import os
import shutil

module1 = Extension('bitunpack', sources = ["bitunpack.c","amaze_demosaic_RT.c", "liblj92/lj92.c"],  extra_compile_args=['-msse2','-std=gnu99'], extra_link_args=[])


setup ( name = "bitunpack", version = "2.0", description = "Fast bit unpacking functions", ext_modules = [module1])


dirName = 'build/'
listOfFiles = list()
for (dirpath, dirnames, filenames) in os.walk(dirName):
    for file in filenames:
        if file.endswith('.so'):
            shutil.move(os.path.join(dirpath, file), '.')

shutil.rmtree('build/')
