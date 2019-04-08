from distutils.core import setup, Extension

module1 = Extension('bitunpack', sources = ["bitunpack.c","liblj92/lj92.c"],  extra_compile_args=['-msse2','-std=gnu99'], extra_link_args=[])


setup ( name = "bitunpack", version = "2.0", description = "Fast bit unpacking functions", ext_modules = [module1])

