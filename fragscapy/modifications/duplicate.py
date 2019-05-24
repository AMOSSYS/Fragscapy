"""
Modification to duplicate one packet (delete it from the packet list).
The duplicate is placed juste after the original one in the list. Can be
either the first one, the last one, a random one or a specific one (by id).
"""
from random import randint
from .mod import Mod

class Duplicate(Mod):
    """
    Duplicate one packet (delete it from the packet list). The duplicate is
    placed juste after the original one in the list. Can be either the first
    one, the last one, a random one or a specific one (by id).
    """
    name = "Duplicate"
    doc = ("Duplicate one of the packets.\n"
           "duplicate {first|last|random|<id>}")
    nb_args = 1

    def __init__(self, *args):
        super().__init__(*args)

        # Check the content of the argument
        self.duplicate_index = None
        if args[0] == "first":
            self.duplicate_index = 0
        elif args[0] == "last":
            self.duplicate_index = -1
        elif args[0] == "random":
            pass  # Duplicate index will be calculated later
        else:
            try:
                self.duplicate_index = int(args[0])
            except ValueError:
                raise ValueError("Parameter 1 unrecognized. "
                                 "Got {}".format(args[0]))

    def apply(self, pkt_list):
        l = len(pkt_list)
        i = self.duplicate_index

        if i is None:  # Random
            i = randint(-l, l-1)

        if i < -l or i > l-1:
            print("Unable to duplicate packet n°{}. PacketList too small."
                  "Passing the modification".format(i))
        else:
            duplicate_packet = pkt_list[i].pkt.copy()
            pkt_list.insert_packet(i, duplicate_packet)

        return pkt_list

    def __str__(self):
        i = self.duplicate_index
        return "{name} {param}".format(
            name=self.name,
            param="random" if i is None else str(i)
        )

    def __repr__(self):
        return "{name}<duplicate_index: {duplicate_index}>".format(
            name=self.name,
            duplicate_index=self.duplicate_index
        )
