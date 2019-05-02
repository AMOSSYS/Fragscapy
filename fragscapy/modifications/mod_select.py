"""mod_select
Select and keeps only some of the packets. The selection is specified by
giving a sequence of the index to keep.
"""
from fragscapy.modifications.mod import Mod
from fragscapy.packet_list import PacketList

MOD_NAME = "Select"
MOD_DOC = ("Select only some packet.\n"
           "select [id1 [id2 [id3 ...]]]")

class ModSelect(Mod):
    """
    Select and keeps only some of the packets. The selection is specified by
    giving a sequence of the index to keep.
    """
    def __init__(self, *args):
        super().__init__(MOD_NAME, MOD_DOC)

        # Checks that all indexes are integer and stores them
        self.sequence = []
        for arg in args:
            try:
                self.sequence.append(int(arg))
            except ValueError:
                raise ValueError("Non integer parameter. "
                                 "Got {}".format(arg))

    def apply(self, pkt_list):
        new_pl = PacketList()
        for i in self.sequence:
            new_pl.add_packet(pkt_list[i].pkt, pkt_list[i].delay)
        return new_pl
