"""Select only some packets and drop the other ones."""

from fragscapy.modifications.mod import Mod
from fragscapy.packetlist import PacketList


class Select(Mod):
    """
    Select and keeps only some of the packets. The selection is specified by
    giving a sequence of the index to keep.
    """
    name = "Select"
    doc = ("Select only some packet.\n"
           "select [id1 [id2 [id3 ...]]]")

    def __init__(self, *args):
        super().__init__(*args)

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

    def __str__(self):
        return "{name} {param}".format(
            name=self.name,
            param=" ".join(str(i) for i in self.sequence)
        )

    def __repr__(self):
        return "{name}<sequence: {sequence}>".format(
            name=self.name,
            sequence=self.sequence
        )
