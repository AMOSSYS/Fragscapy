"""
Modifies the `Payload Length` field of the IPv6 packet.
"""
from random import randint
from .mod import Mod

class Ipv6Length(Mod):
    """
    Modifies the `Payload Length` field of the IPv6 packet.
    """
    name = "IPv6length"
    doc = ("Modifies the `Payload Length` field of the IPv6 packet.\n"
           "ipv6_length {random|<fixed_length>}")
    nb_args = 1

    def __init__(self, *args):
        super().__init__(*args)

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

    def apply(self, pkt_list):
        """
        Fetches the IPv6 layer replace the payload length parameter.

        :param pkt_list: The packet list.
        """
        l = self.length
        if l is None:
            l = randint(0, 0xffff)

        for pkt in pkt_list:
            pkt['Ipv6'].plen = l

        return pkt_list

    def __str__(self):
        return "{name} {param}".format(
            name=self.name,
            param="random" if self.length is None else str(self.length)
        )

    def __repr__(self):
        return "{name}<length: {length}>".format(
            name=self.name,
            length=self.length
        )
