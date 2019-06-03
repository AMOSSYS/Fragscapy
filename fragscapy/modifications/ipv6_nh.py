"""Modifies the 'Next Header' field of the IPv6 packet."""

import random

from fragscapy.modifications.mod import Mod


class Ipv6Nh(Mod):
    """Modifies the 'Next Header' field of the IPv6 packet.

    Args:
        *args: The arguments of the mods.

    Attributes:
        proto: The new value for the 'Next Header' field. None if random.

    Raises:
        ValueError: Unrecognized or incorrect number of parameters.

    Examples:
        >>> Ipv6NextHeader(4).proto
        4
    """

    name = "Ipv6Nh"
    doc = ("Modifies the 'Next Header' field of the IPv6 packet.\n"
           "ipv6_nh {random|<protocol_number>}")
    _nb_args = 1

    def __init__(self, *args):
        super().__init__(*args)

        self.proto = None
        if args[0] == "random":
            pass  # Protocol number will be calculated later
        else:
            try:
                self.proto = int(args[0])
            except ValueError:
                raise ValueError("Parameter 1 unrecognized. "
                                 "Got {}".format(args[0]))
            if self.proto > 0xff or self.proto < 0:
                raise ValueError("Parameter 1 must be beetween 0 and 255. "
                                 "Got {}".format(self.proto))

    def apply(self, pkt_list):
        """Modifies the 'Next Header' field of the IPv6 packet. See `Mod.apply`
        for more details."""
        nh = self.proto
        if nh is None:
            nh = random.randint(0, 0xff)

        for pkt in pkt_list:
            pkt['Ipv6'].nh = nh

        return pkt_list

    def __str__(self):
        return "{name} {param}".format(
            name=self.name,
            param="random" if self.proto is None else str(self.proto)
        )

    def __repr__(self):
        return "{name}<proto: {proto}>".format(
            name=self.name,
            proto=self.proto
        )
