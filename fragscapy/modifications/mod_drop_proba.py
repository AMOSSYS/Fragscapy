"""mod_drop_proba
Modification to drop each packet (delete them from the packet list).
The parameter is the probability for each packet to be dropped.
"""
from random import random
from fragscapy.modifications.mod import Mod

MOD_NAME = "DropProba"
MOD_DOC = ("Drop each packet with a certain probability.\n"
           "dropmulti <proba>")

class ModDropProba(Mod):
    """
    Drop each packet (delete it from the packet list).
    The parameter is the probability for each packet to be dropped.
    """
    def __init__(self, *args):
        super().__init__(MOD_NAME, MOD_DOC)

        # Check number of arguments
        if len(args) != 1:
            raise ValueError("Incorrect number of parameters specified. "
                             "Got {}, expected 1".format(len(args)))

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
