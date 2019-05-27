"""fragscapy
Simple module aiming at reproducing fragroute behavior but with Scapy packets.
The idea is to create a list of "modifications" (`ModList`) that can be
applied to a series of Scapy packets (`PacketList`). The result is another
series of Scapy packets modified according to the "modifications".
"""
__author__ = "Maël KERVELLA"
__version__ = "v0.1"
