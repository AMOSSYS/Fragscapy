"""Modifies the 'Hop Limit' field of the IPv6 packet."""

import random

from fragscapy.modifications.mod import Mod


class Ipv6Hop(Mod):
    """Modifies the 'Hop Limit' field of the IPv6 packet.

    Args:
        *args: The arguments of the mods.

    Attributes:
        hop: The new value for the 'Hop Limit' field. None if random.

    Raises:
        ValueError: Unrecognized or incorrect number of parameters.

    Examples:
        >>> Ipv6Hop(0x01).hop
        1
    """

    name = "Ipv6Hop"
    doc = ("Modifies the 'Hop Limit' field of the IPv6 packet.\n"
           "ipv6_hop {random|<fixed_hop>}")
    _nb_args = 1

    def __init__(self, *args):
        super().__init__(*args)

        self.hop = None
        if args[0] == "random":
            pass  # Protocol number will be calculated later
        else:
            try:
                self.hop = int(args[0])
            except ValueError:
                raise ValueError("Parameter 1 unrecognized. "
                                 "Got {}".format(args[0]))
            if self.hop > 0xff or self.hop < 0:
                raise ValueError("Parameter 1 must be beetween 0 and 255. "
                                 "Got {}".format(self.hop))

    def apply(self, pkt_list):
        """
        Fetches the IPv6 layer replace the hop parameter.

        :param pkt_list: The packet list.
        """
        h = self.hop
        if h is None:
            h = random.randint(0, 0xff)

        for pkt in pkt_list:
            pkt['Ipv6'].hlim = h

        return pkt_list

    def __str__(self):
        return "{name} {param}".format(
            name=self.name,
            param="random" if self.hop is None else str(self.hop)
        )

    def __repr__(self):
        return "{name}<hop: {hop}>".format(
            name=self.name,
            hop=self.hop
        )
