# setup.py

from Cython.Build import cythonize
from setuptools import setup

setup(
    ext_modules=cythonize("stemdata/find_flexions.pyx"),
)
