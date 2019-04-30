"""mod_drop_one
Modification to drop one packet (delete it from the packet list). Can be
either the first one, the last one, a random one or a specific one (by id).
"""
from random import randint
from modification import Modification

MOD_NAME = "DropOne"
MOD_DOC = ("Drop one of the packets.\n"
           "dropone {first|last|random|<id>}")

class ModDropOne(Modification):
    """
    Drop a single packet (delete it from the packet list). Can be either the
    first one, the last one, a random one or a specific one (by id).
    """
    def __init__(self, *args):
        super().__init__(MOD_NAME, MOD_DOC)

        # Check number of arguments
        if len(args) != 1:
            raise ValueError("Incorrect number of parameters specified. "
                             "Got {}, expected 1".format(len(args)))

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
        l = len(pkt_list)
        i = self.drop_index

        if i is None:  # Random
            i = randint(-l, l-1)

        if i < -l or i > l-1:
            print("Unable to drop packet n°{}. PacketList too small."
                  "Passing the modification".format(i))
        else:
            pkt_list.remove_packet(i)
