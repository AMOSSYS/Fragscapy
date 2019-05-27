"""fragscapy
Simple module aiming at reproducing fragroute behavior but with Scapy packets.
The idea is to create a list of "modifications" (`ModList`) that can be
applied to a series of Scapy packets (`PacketList`). The result is another
series of Scapy packets modified according to the "modifications".
"""
import logging
from scapy.config import conf

# Removes warning messages
logging.getLogger("scapy.runtime").setLevel(logging.ERROR)
# Removes verbose send messages
conf.verb = 0
