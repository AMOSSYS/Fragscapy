"""
Modification to drop each packet (delete them from the packet list).
The parameter is the probability for each packet to be dropped.
"""
from random import random
from .mod import Mod

class DropProba(Mod):
    """
    Drop each packet (delete it from the packet list).
    The parameter is the probability for each packet to be dropped.
    """
    name = "DropProba"
    doc = ("Drop each packet with a certain probability.\n"
           "dropproba <proba>")
    nb_args = 1

    def __init__(self, *args):
        super().__init__(*args)


        # Check the content of the argument
        try:
            self.drop_proba = float(args[0])
        except ValueError:
            raise ValueError("Parameter 1 should be between 0 and 1. "
                             "Got {}".format(args[0]))

        if self.drop_proba < 0 or self.drop_proba > 1:
            raise ValueError("Parameter 1 should be between 0 and 1. "
                             "Got {}".format(args[0]))


    def apply(self, pkt_list):
        # The function to determine if the packet should be kept
        condition = lambda _: random() < self.drop_proba
        # A list of decreasing indexes that should be removed
        to_remove = [i for i in range(len(pkt_list)-1, -1, -1) if condition(pkt_list[i])]
        # Remove the indexes (in decreasing order)
        for i in to_remove:
            pkt_list.remove_packet(i)

        return pkt_list

    def __str__(self):
        return "{name} {param}".format(
            name=self.name,
            param=str(self.drop_proba)
        )

    def __repr__(self):
        return "{name}<drop_proba: {drop_proba}>".format(
            name=self.name,
            drop_proba=self.drop_proba
        )