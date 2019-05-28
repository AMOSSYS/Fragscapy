#!/usr/bin/env python3

import os
try:
    from setuptools import setup, find_packages
except ImportError:
    from distutils.core import setup

    def find_packages(where='.'):
        # os.walk -> list[(dirname, list[subdirs], list[files])]
        return [folder.replace("/", ".").lstrip(".")
                for (folder, _, fils) in os.walk(where)
                if "__init__.py" in fils]
import sys
from io import open as io_open

# Get version from fragscapy/_version.py
__version__ = None
src_dir = os.path.abspath(os.path.dirname(__file__))
version_file = os.path.join(src_dir, 'fragscapy', '_version.py')
with io_open(version_file, mode='r') as fd:
    exec(fd.read())

requires = []
with io_open("requirements.txt", mode='r') as fh:
    requires = [line.strip().split('#', 1)[0].strip()
                for line in fd.readlines()]

long_description = ""
with io_open("README.md", mode='r') as fh:
    long_description = fh.read()

setup(name='Fragscapy',
      version=__version__,
      author='Maël Kervella',
      author_email='dev@maelkervella.eu',
      description="Catch and modify network packets on the fly with Scapy",
      long_description=long_description,
      long_description_content_type="text/markdown",
      url='https://gitlab.amossys.fr/mka/fragscapy',
      packages=find_packages(),
      requires=requires
      classifiers=[
          "Development Status :: 4 - Beta",
          "Environment :: Console",
          "Intended Audience :: Developers",
          "Intended Audience :: Information Technology",
          "Intended Audience :: Science/Research",
          "Intended Audience :: System Administrators",
          "Intended Audience :: Telecomunications Industry",
          "Programming Laguage :: Python :: 3",
          "Operating System :: POSIX :: Linux",
          "Topic :: Internet",
          "Topic :: Security",
          "Topic :: System :: Networking",
          "Topic :: System :: Networking :: Monitoring",
      ],
      keywords='scapy fragroute nfqueue firewall evaluation network packets',
      )
