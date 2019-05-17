#!/usr/bin/env python3

from setuptools import setup

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(name='FragScapy',
      version='0.1',
      author='Maël Kervella',
      author_email='dev@maelkervella.eu',
      description='Utility to mess up with fragmentation and Scapy packets',
      long_description=long_description,
      long_description_content_type="text/markdown",
      url='https://gitlab.amossys.fr/mka/fragscapy',
      packages=['fragscapy', 'fragscapy.modifications'],
      requires=[
          'scapy',
          'fnfqueue',
      ],
      classifiers=[
          "Development Status :: 3 - Alpha",
          "Environment :: Console",
          "Intended Audience :: Developers",
          "Intended Audience :: Information Technology",
          "Intended Audience :: Science/Research",
          "Intended Audience :: System Administrators",
          "Intended Audience :: Telecomunications Industry",
          "Programming Laguage :: Python :: 3",
          "Operating System :: OS Independant",
          "Topic :: Security",
          "Topic :: System :: Networking",
          "Topic :: System :: Networking :: Monitoring",
      ],
      )
