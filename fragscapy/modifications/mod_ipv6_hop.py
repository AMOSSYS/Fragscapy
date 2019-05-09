"""mod_ipv6_hop
Modifies the `Hop Limit` field of the IPv6 packet.
"""
from random import randint
from fragscapy.modifications.mod import Mod

class ModIPv6Hop(Mod):
    """ModIPv6Hop
    Modifies the `Hop Limit` field of the IPv6 packet.
    """
    name = "IPv6Hop"
    doc = ("Modifies the `Hop Limit` field of the IPv6 packet.\n"
           "ipv6_hop {random|<fixed_hop>}")
    nb_args = 1

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
        """apply
        Fetches the IPv6 layer replace the hop parameter.

        :param pkt_list: The packet list.
        """
        h = self.hop
        if h is None:
            h = randint(0, 0xff)

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
