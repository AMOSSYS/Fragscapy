#!/usr/bin/env python3

from distutils.core import setup

setup(name='FragScapy',
      version='0.1',
      description='Utility to mess up with fragmentation and Scapy packets',
      author='Maël Kervella',
      author_email='dev@maelkervella.eu',
      url='https://gitlab.amossys.fr/mka/fragscapy',
      packages=['fragscapy', 'fragscapy.modifications'],
      requires=[
          'scapy'
      ])
