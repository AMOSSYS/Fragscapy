"""Segments the TCP packets at the L4-layer."""

import scapy.layers.inet
import scapy.packet

from fragscapy.modifications.mod import Mod
from fragscapy.modifications.utils import tcp_segment
from fragscapy.packetlist import PacketList


class TcpSegment(Mod):
    """Segments the TCP packets at the L4-layer.

    The segmentation size must be specified. It represents the size of the
    TCP data  in each of the fragments.

    Args:
        *args: The arguments of the mods.

    Attributes:
        segmentsize: The segmentation size (bytes of TCP data to use).

    Raises:
        ValueError: Unrecognized or incorrect number of parameters.

    Examples:
        >>> TcpSegment(32).segmentsize
        32
    """

    name = "TcpSegment"
    doc = ("Segments the TCP packets at the L4-layer\n"
           "tcp_segment <segmentsize>")
    _nb_args = 1

    def parse_args(self, *args):
        """See base class."""
        try:
            self.segmentsize = int(args[0])
        except ValueError:
            raise ValueError("Parameter 1 unrecognized. "
                             "Got '{}'".format(args[0]))
        if self.segmentsize < 0:
            raise ValueError("'segmentsize' shoudl be positive. "
                             "Got '{}'".format(self.segmentsize))

    def apply(self, pkt_list):
        """Segments each TCP packet. See `Mod.apply` for more details."""
        new_pl = PacketList()

        for pkt in pkt_list:
            if pkt.pkt.haslayer('TCP'):
                segments = tcp_segment(pkt.pkt, self.segmentsize)

                index = len(new_pl) - 1
                for segment in segments:
                    new_pl.add_packet(segment)
                new_pl.edit_delay(index, pkt.delay)
            else:
                # Not TCP so no segmentation
                new_pl.add_packet(segment, pkt.delay)

        return new_pl
