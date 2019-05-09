"""fragscapy
Simple module aiming at reproducing fragroute behavior but with Scapy packets.
The idea is to create a list of "modifications" (`ModList`) that can be
applied to a series of Scapy packets (`PacketList`). The result is another
series of Scapy packets modified according to the "modifications".
"""
import logging
from scapy.config import conf
from fragscapy.modifications import (
    ModList, ModDropOne, ModDropProba, ModEcho, ModPrint, ModDuplicate,
    ModReorder, ModSelect, ModFragment6, ModIPv6ExtHdrMixup, ModIPv6Hop,
    ModIPv6Length, ModIPv6NH)
from fragscapy.packet_list import PacketList

# Removes warning messages
logging.getLogger("scapy.runtime").setLevel(logging.ERROR)
# Removes verbose send messages
conf.verb = 0

__all__ = ['ModList', 'ModDropOne', 'ModDropProba', 'ModEcho', 'ModPrint',
           'ModDuplicate', 'ModReorder', 'ModSelect', 'ModFragment6',
           'ModIPv6ExtHdrMixup', 'ModIPv6Hop', 'ModIPv6Length', 'ModIPv6NH',
           'PacketList']
