"""
Modifies the `Next Header` field of the IPv6 packet.
"""
from random import randint
from .mod import Mod

class IPv6NH(Mod):
    """
    Modifies the `Next Header` field of the IPv6 packet.
    """
    name = "IPv6NH"
    doc = ("Modifies the `Next Header` field of the IPv6 packet.\n"
           "ipv6_nh {random|<protocol_number>}")
    nb_args = 1

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
        """
        Fetches the IPv6 layer replace the nh parameter.

        :param pkt_list: The packet list.
        """
        nh = self.proto
        if nh is None:
            nh = randint(0, 0xff)

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
