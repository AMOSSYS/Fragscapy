"""Drops each packet with a certain probability."""

import random

from fragscapy.modifications.mod import Mod


class DropProba(Mod):
    """Drops each packet with a certain probability.

    Delete the packet from the packet list. The parameter is the
    probability for each packet to be dropped.

    Args:
        *args: The arguments of the mods.

    Attributes:
        drop_proba: The probability with which a packet is to be dropped.
            None if random.

    Raises:
        ValueError: Unrecognized or incorrect number of parameters.

    Examples:
        >>> DropProba(0.25).drop_proba
        0.25
    """

    name = "DropProba"
    doc = ("Drops each packet with a certain probability.\n"
           "dropproba <proba>")
    _nb_args = 1

    def parse_args(self, *args):
        """See base class."""
        try:
            self.drop_proba = float(args[0])
        except ValueError:
            raise ValueError("Parameter 1 should be between 0 and 1. "
                             "Got {}".format(args[0]))

        if self.drop_proba < 0 or self.drop_proba > 1:
            raise ValueError("Parameter 1 should be between 0 and 1. "
                             "Got {}".format(args[0]))

    def is_deterministic(self):
        """See base class."""
        return False

    def apply(self, pkt_list):
        """Drops each packet with a certain probability. See `Mod.apply` for
        more details."""
        # The function to determine if the packet should be kept
        condition = lambda _: random.random() < self.drop_proba
        # A list of decreasing indexes that should be removed
        to_remove = [i for i in range(len(pkt_list)-1, -1, -1)
                     if condition(pkt_list[i])]
        # Remove the indexes (in decreasing order)
        for i in to_remove:
            pkt_list.remove_packet(i)

        return pkt_list
