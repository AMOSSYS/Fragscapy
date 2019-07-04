"""Segments the TCP packets at the L4-layer."""

import random

import scapy.layers.inet
import scapy.packet

from fragscapy.modifications.mod import Mod
from fragscapy.modifications.utils import tcp_segment
from fragscapy.packetlist import PacketList


class TcpOverlap(Mod):
    """Creates overlapping TCP segments.

    Args:
        *args: The arguments of the mods.

    Attributes:
        segmentsize: The segmentation size (bytes of TCP data to use).
        overlapsize: The size of the random_data that will be added
        append_before: True if the random_data should be added before the
            packet.

    Raises:
        ValueError: Unrecognized or incorrect number of parameters.

    Examples:
        >>> TcpOverlap(32, 8, "before").segmentsize
        32
        >>> TcpOverlap(32, 8, "before").overlapsize
        8
        >>> TcpOverlap(32, 9, "before").append_before
        True
    """

    name = "TcpOverlay"
    doc = ("Creates overlapping TCP segments\n"
           "tcp_segment <segmentsize> <overlapsize> <append>\n"
           "  - 'segmentsize' is the segmentation size in octets to use\n"
           "        (i.e. the size of the TCP payload per segment)\n"
           "  - 'overlapsize' is the the size in octets of random data that\n"
           "        overlaps\n"
           "  - 'append' is either 'before' of 'after' and indicates where to\n"
           "        add the random data that overlaps.\n"
           "The final size of the TCP payload is 'fragsize + overlapsize'")
    _nb_args = 3

    def parse_args(self, *args):
        """See base class."""
        try:
            self.segmentsize = int(args[0])
        except ValueError:
            raise ValueError("Parameter 1 unrecognized. "
                             "Got '{}'".format(args[0]))
        if self.segmentsize < 0:
            raise ValueError("'segmentsize' should be positive. "
                             "Got '{}'".format(self.segmentsize))

        try:
            self.overlapsize = int(args[1])
        except ValueError:
            raise ValueError("Parameter 2 unrecognized. "
                             "Got '{}'".format(args[1]))
        if self.overlapsize < 0:
            raise ValueError("'overlapsize' should be positive. "
                             "Got '{}'".format(self.overlapsize))

        if args[2].lower() == "after":
            self.overlap_before = False
        elif args[2].lower() == "before":
            self.overalp_before = True
        else:
            raise ValueError("'overlap' should be either 'after' or 'before'. "
                             "Got '{}'".format(args[2]))

    def apply(self, pkt_list):
        """Segments each TCP packet. See `Mod.apply` for more details."""
        new_pl = PacketList()

        for pkt in pkt_list:
            if pkt.pkt.haslayer('TCP'):
                random_data = bytes(random.randrange(0, 0xff)
                                    for _ in range(self.overlapsize))
                segments = tcp_segment(pkt.pkt, self.segmentsize,
                                       random_data, self.overlap_before)

                index = len(new_pl) - 1
                for segment in segments:
                    new_pl.add_packet(segment)
                new_pl.edit_delay(index, pkt.delay)
            else:
                # Not TCP so no segmentation
                new_pl.add_packet(segment, pkt.delay)

        return new_pl
