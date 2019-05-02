"""mod_reorder
Modification to reorder the packet list. The operation can either
reverse the whole packet list or simply randomly rearrange them.
"""
from random import shuffle
from enum import Enum
from fragscapy.modifications.mod import Mod
from fragscapy.packet_list import PacketList

MOD_NAME = "Reorder"
MOD_DOC = ("Reorder the packet list.\n"
           "reorder {reverse|random}")
METHOD = Enum("METHOD", "REVERSE RANDOM")

class ModReorder(Mod):
    """
    Reorder the packet list. The operation can either reverse the whole
    packet list or simply randomly rearrange them.
    """
    def __init__(self, *args):
        super().__init__(MOD_NAME, MOD_DOC)

        # Check number of arguments
        if len(args) != 1:
            raise ValueError("Incorrect number of parameters specified. "
                             "Got {}, expected 1".format(len(args)))

        # Check the content of the argument
        if args[0] == "reverse":
            self.method = METHOD.REVERSE
        elif args[0] == "random":
            self.method = METHOD.RANDOM
        else:
            raise ValueError("Parameter 1 unrecognized. "
                             "Got {}".format(args[0]))

    def apply(self, pkt_list):
        if self.method == METHOD.REVERSE:
            sequence = list(range(len(pkt_list)-1, -1, -1))
        elif self.method == METHOD.RANDOM:
            sequence = list(range(len(pkt_list)))
            shuffle(sequence)
        new_pl = PacketList()
        for i in sequence:
            new_pl.add_packet(pkt_list[i].pkt, pkt_list[i].delay)
        return new_pl
