"""Modifies the 'Payload Length' field of the IPv6 packet."""

import random

from fragscapy.modifications.mod import Mod


class Ipv6Length(Mod):
    """Modifies the 'Payload Length' field of the IPv6 packet.

    Args:
        *args: The arguments of the mods.

    Attributes:
        length: The new value for the 'Payload Length' field. None if random.

    Raises:
        ValueError: Unrecognized or incorrect number of parameters.

    Examples:
        >>> Ipv6Length(0xff).length
        255
    """

    name = "Ipv6Length"
    doc = ("Modifies the 'Payload Length' field of the IPv6 packet.\n"
           "ipv6_length {random|<fixed_length>}")
    _nb_args = 1

    def __init__(self, *args):
        super().__init__(*args)

    def parse_args(self, *args):
        """See base class."""
        self.length = None
        if args[0] == "random":
            pass  # Protocol number will be calculated later
        else:
            try:
                self.length = int(args[0])
            except ValueError:
                raise ValueError("Parameter 1 unrecognized. "
                                 "Got {}".format(args[0]))
            if self.length > 0xffff or self.length < 0:
                raise ValueError("Parameter 1 must be beetween 0 and 65535. "
                                 "Got {}".format(self.length))

    def is_deterministic(self):
        """See base class."""
        return self.length is not None  # i.e. not random

    def apply(self, pkt_list):
        """Modifies the 'Payload Length' field of each IPv6 packet. See
        `Mod.apply` for more details."""
        l = self.length
        if l is None:
            l = random.randint(0, 0xffff)

        for pkt in pkt_list:
            pkt['Ipv6'].plen = l

        return pkt_list

    def get_params(self):
        """See base class."""
        return {k: v if v is not None else "random"
                for k, v in super(Ipv6Length, self).get_params().items()}
