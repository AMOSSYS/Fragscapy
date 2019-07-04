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

    def parse_args(self, *args):
        """See base class."""
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

    def is_deterministic(self):
        """See base class."""
        return self.drop_index is not None  # i.e. not random

    def apply(self, pkt_list):
        """Drops one packet. See `Mod.apply` for more details."""
        l = len(pkt_list)
        if not l:  # Avoid the trivial case
            return pkt_list

        i = self.drop_index

        if i is None:  # Random
            if l == 1:  # Avoid the case of randint(0, 0)
                i = 0
            else:
                i = random.randint(-l, l-1)

        if i >= -l and i <= l-1:
            pkt_list.remove_packet(i)

        return pkt_list

    def get_params(self):
        """See base class."""
        return {k: v if v is not None else "random"
                for k, v in super(DropOne, self).get_params().items()}
