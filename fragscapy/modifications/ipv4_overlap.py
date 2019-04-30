"""Creates overlapping fragments of the packets."""

import random

import scapy.layers.inet

from fragscapy.modifications.mod import Mod
from fragscapy.packetlist import PacketList


class Ipv4Overlap(Mod):
    """Creates overlapping fragments of the packets

    Args:
        *args: The argument of the mods.

    Attributes:
        fragsize: The fragmentation size (maximum length of a fragment if
            there was no overlapping).
        overlapsize: The size of the random_data added that will overlap.

    Raises:
        ValueError: Unrecognized or incorrect number of parameters.

    Examples:
        >>> Ipv4Overlap(64, 32).fragsize
        64
        >>> Ipv4Overlap(64, 32).overlapsize
        32
    """

    name = "Ipv4Overlap"
    doc = ("Creates overlapping fragments of the packets.\n"
           "ipv4overlap <fragsize> <overlapsize>\n"
           "  - 'fragsize' is the fragmentation size in octets to use\n"
           "        (not the size of the final packets but the size of the\n"
           "        packets as if there was no overlapping)\n"
           "  - 'overlapsize' is the size in octets of random data that\n"
           "        overlaps\n"
           "The final size of the packets is 'fragsize + overlapsize'.")

    def parse_args(self, *args):
        try:
            self.fragsize = int(args[0])
        except ValueError:
            raise ValueError("Parameter 1 unrecognized. "
                             "Got '{}'".format(args[0]))
        if self.fragsize < 0:
            raise ValueError("'fragsize' should be positive."
                             "Got '{}'".format(self.fragsize))

        try:
            self.overlap = int(args[1])
        except ValueError:
            raise ValueError("Parameter 2 unrecognized. "
                             "Got '{}'".format(args[1]))
        if self.overlap < 0:
            raise ValueError("'overlap' should be positive."
                             "Got '{}'".format(self.overlap))


    def apply(self, pkt_list):
        new_pl = PacketList()

        for pkt in pkt_list:
            if pkt.pkt.haslayer('IP'):
                fragments = scapy.layers.inet.fragment(pkt.pkt, self.fragsize)

                index = len(new_pl) - 1
                for fragment in fragments:
                    random_data = bytes(random.randrange(0, 0xff)
                                        for _ in range(self.overlap))
                    fragment = fragment/random_data
                    new_pl.add_packet(fragment)
                new_pl.edit_delay(index, pkt.delay)
            else:
                new_pl.add_packet(fragment, pkt.delay)

        return new_pl
