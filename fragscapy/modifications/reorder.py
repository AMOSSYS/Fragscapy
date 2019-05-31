"""Reorder the packet listing."""

import enum
import random

from fragscapy.modifications.mod import Mod
from fragscapy.packetlist import PacketList


METHOD = enum.Enum("METHOD", "REVERSE RANDOM")


class Reorder(Mod):
    """
    Reorder the packet list. The operation can either reverse the whole
    packet list or simply randomly rearrange them.
    """
    name = "Reorder"
    doc = ("Reorder the packet list.\n"
           "reorder {reverse|random}")
    nb_args = 1

    def __init__(self, *args):
        super().__init__(*args)

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
            random.shuffle(sequence)
        new_pl = PacketList()
        for i in sequence:
            new_pl.add_packet(pkt_list[i].pkt, pkt_list[i].delay)
        return new_pl

    def __str__(self):
        return "{name} {param}".format(
            name=self.name,
            param="reverse" if self.method == METHOD.REVERSE else "random"
        )

    def __repr__(self):
        return "{name}<method: {method}>".format(
            name=self.name,
            method=self.method
        )
