"""Drops one of the packets."""

import random

from fragscapy.modifications.mod import Mod


class DropOne(Mod):
    """Drops one of the packets.

    Delete the packet from the packet list. Can be either the first one, the
    last one, a random one or a specific one (by id).

    Args:
        *args: The arguments of the mods.

    Attributes:
        drop_index: The index to drop. None if random.

    Raises:
        ValueError: Unrecognized or incorrect number of parameters.

    Examples:
        >>> DropOne("first").drop_index
        0
        >>> DropOne(42).drop_index
        42
    """

    name = "DropOne"
    doc = ("Drop one of the packets.\n"
           "dropone {first|last|random|<id>}")
    _nb_args = 1

    def __init__(self, *args):
        super().__init__(*args)

        # Check the content of the argument
        self.drop_index = None
        if args[0] == "first":
            self.drop_index = 0
        elif args[0] == "last":
            self.drop_index = -1
        elif args[0] == "random":
            pass  # Drop index will be calculated later
        else:
            try:
                self.drop_index = int(args[0])
            except ValueError:
                raise ValueError("Parameter 1 unrecognized. "
                                 "Got {}".format(args[0]))

    def apply(self, pkt_list):
        """Drops one packet. See `Mod.apply` for more details."""
        l = len(pkt_list)
        i = self.drop_index

        if i is None:  # Random
            i = random.randint(-l, l-1)

        if i < -l or i > l-1:
            print("Unable to drop packet n°{}. PacketList too small."
                  "Passing the modification".format(i))
        else:
            pkt_list.remove_packet(i)

        return pkt_list

    def __str__(self):
        return "{name} {param}".format(
            name=self.name,
            param="random" if self.drop_index is None else str(self.drop_index)
        )

    def __repr__(self):
        return "{name}<drop_index: {drop_index}>".format(
            name=self.name,
            drop_index=self.drop_index
        )
