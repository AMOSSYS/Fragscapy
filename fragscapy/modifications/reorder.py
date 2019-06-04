"""Reorder the packet listing."""

import enum
import random

from fragscapy.modifications.mod import Mod
from fragscapy.packetlist import PacketList


METHOD = enum.Enum("METHOD", "REVERSE RANDOM")


class Reorder(Mod):
    """Reorder the packet listing.

    The operation can either reverse the whole packet list or simply
    randomly rearrange them.

    Args:
        *args: The arguments of the mods.

    Attributes:
        method: The method to use (reverse or random)

    Raises:
        ValueError: Unrecognized or incorrect number of parameters.

    Examples:
        >>> Reorder("reverse").method
        REVERSE
        >>> Reorder("random").method
        RANDOM
    """

    name = "Reorder"
    doc = ("Reorder the packet list.\n"
           "reorder {reverse|random}")
    _nb_args = 1

    def parse_args(self, *args):
        """See base class."""
        if args[0] == "reverse":
            self.method = METHOD.REVERSE
        elif args[0] == "random":
            self.method = METHOD.RANDOM
        else:
            raise ValueError("Parameter 1 unrecognized. "
                             "Got {}".format(args[0]))

    def is_deterministic(self):
        """See base class."""
        return self.method != METHOD.RANDOM

    def apply(self, pkt_list):
        """Reorder the packets. See `Mod.apply` for more details."""
        if self.method == METHOD.REVERSE:
            sequence = list(range(len(pkt_list)-1, -1, -1))
        elif self.method == METHOD.RANDOM:
            sequence = list(range(len(pkt_list)))
            random.shuffle(sequence)
        new_pl = PacketList()
        for i in sequence:
            new_pl.add_packet(pkt_list[i].pkt, pkt_list[i].delay)
        return new_pl
