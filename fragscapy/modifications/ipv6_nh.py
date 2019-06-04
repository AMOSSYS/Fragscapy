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

    def parse_args(self, *args):
        """See base class."""
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

    def is_deterministic(self):
        """See base class."""
        return self.proto is not None  # i.e. not random

    def apply(self, pkt_list):
        """Modifies the 'Next Header' field of the IPv6 packet. See `Mod.apply`
        for more details."""
        nh = self.proto
        if nh is None:
            nh = random.randint(0, 0xff)

        for pkt in pkt_list:
            pkt['Ipv6'].nh = nh

        return pkt_list

    def get_params(self):
        """See base class."""
        return {k: v if v is not None else "random"
                for k, v in super(Ipv6Nh, self).get_params().items()}
