"""Adds delay before one or all the packets."""

import enum
import random

from fragscapy.modifications.mod import Mod


METHOD = enum.Enum("METHOD", "FIRST LAST RANDOM ID ALL")


class Delay(Mod):
    """Adds delay before one or all the packets.

    This modification can add delay to one of the packets (specified either by
    'first', 'last', 'random' or id) or to each one of the packets
    (specified by 'all').

    Note that if the first packet is delayed, all the following packets are
    automatically delayed because they are send after the first one.

    Args:
        *args: The arguments of the mods.

    Attributes:
        delay_all: True if all packets are to be delayed
        delay_index: The index of the packet to delay
        delay: the delay to add in seconds

    Raises:
        ValueError: Unrecognized or incorrect number of parameters.

    Examples:
        >>> Delay("first", 3).delay_index
        0
        >>> Delay("first", 3).delay
        3
        >>> Delay("all", 1).delay_all
        True
    """

    name = "Delay"
    doc = ("Add some delay (in seconds) before one of or all the packets.\n"
           "delay {first|last|random|all|<id>} <delay>")
    _nb_args = 2

    def parse_args(self, *args):
        """See base class."""
        self.delay_index = None
        self.delay_all = False

        # Parse arg1
        if args[0] == "first":
            self.delay_index = 0
        elif args[0] == "last":
            self.delay_index = -1
        elif args[0] == "random":
            pass  # Drop index will be calculated later
        elif args[0] == "all":
            self.delay_all = True
        else:
            try:
                self.delay_index = int(args[0])
            except ValueError:
                raise ValueError("Parameter 1 unrecognized. "
                                 "Got {}".format(args[0]))

        # Parse arg2
        try:
            self.delay = float(args[1])
        except ValueError:
            raise ValueError("Parameter 2 unrecognized. "
                             "Got {}".format(args[1]))

    def is_deterministic(self):
        """See base class."""
        return self.delay_all or self.delay_index is not None

    def apply(self, pkt_list):
        """Delays the correct packet(s). See `Mod.apply` for more details."""
        l = len(pkt_list)

        if self.delay_all:
            for i in range(l):
                pkt_list.edit_delay(i, self.delay)
        else:
            i = self.delay_index

            if i is None:  # Random
                i = random.randint(-l, l-1)

            if i < -l or i > l-1:
                print("Unable to drop packet n°{}. PacketList too small."
                      "Passing the modification".format(i))
            else:
                pkt_list.edit_delay(i, self.delay)

        return pkt_list

    def get_params(self):
        """See base class."""
        return {k: v if v is not None else "random"
                for k, v in super(Delay, self).get_params().items()}
