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
from io import open as io_open

# Get version from fragscapy/_version.py
__version__ = None
src_dir = os.path.abspath(os.path.dirname(__file__))
version_file = os.path.join(src_dir, 'fragscapy', '_version.py')
with io_open(version_file, mode='r') as fh:
    exec(fh.read())

requirements = []
with io_open("requirements.txt", mode='r') as fh:
    requirements = [line.strip().split('#', 1)[0].strip()
                    for line in fh.readlines()]

requirements_doc = []
with io_open("requirements-doc.txt", mode='r') as fh:
    requirements_doc = [line.strip().split('#', 1)[0].strip()
                        for line in fh.readlines()]

long_description = ""
with io_open("README.md", mode='r') as fh:
    long_description = fh.read()

setup(name='fragscapy',
      version=__version__,
      author='Maël Kervella',
      author_email='dev@maelkervella.eu',
      description="Catch and modify network packets on the fly with Scapy",
      long_description=long_description,
      long_description_content_type="text/markdown",
      license="MIT License",
      url='https://github.com/AMOSSYS/Fragscapy',
      packages=['fragscapy'] + ['fragscapy.'+i for i in find_packages('fragscapy')],
      install_requires=requirements,
      extra_requires=requirements_doc,
      package_data={
          'fragscapy': ['README.md', 'LICENSE.txt', 'config_examples/*'],
      },
      entry_points={
          'console_scripts': [
              'fragscapy=fragscapy:main',
          ],
      },
      platforms=['Linux'],
      classifiers=[
          "Development Status :: 4 - Beta",
          "Environment :: Console",
          "Intended Audience :: Developers",
          "Intended Audience :: Information Technology",
          "Intended Audience :: Science/Research",
          "Intended Audience :: System Administrators",
          "Intended Audience :: Telecomunications Industry",
          "License :: OSI Approved :: MIT License",
          "Operating System :: POSIX :: Linux",
          "Programming Laguage :: Python :: 3",
          "Topic :: Internet",
          "Topic :: Security",
          "Topic :: System :: Networking",
          "Topic :: System :: Networking :: Monitoring",
      ],
      keywords='scapy fragroute nfqueue firewall evaluation network packets',
     )
