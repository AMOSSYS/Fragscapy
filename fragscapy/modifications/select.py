"""Selects only some packets and drop the other ones."""

from fragscapy.modifications.mod import Mod
from fragscapy.packetlist import PacketList


class Select(Mod):
    """Selects only some packets and drop the other ones.

    The selection is specified by giving a sequence of the index to keep.

    Args:
        *args: The arguments of the mods.

    Attributes:
        sequence: A list of the index to keep.

    Raises:
        ValueError: Unrecognized or incorrect number of parameters.

    Examples:
        >>> Select(0, 2, 4, 6, 8).sequence
        [0, 2, 4, 6, 8]
        >>> Select().sequence
        []
    """

    name = "Select"
    doc = ("Select only some packet.\n"
           "select [id1 [id2 [id3 ...]]]")

    def parse_args(self, *args):
        """See base class."""
        self.sequence = []
        for arg in args:
            try:
                self.sequence.append(int(arg))
            except ValueError:
                raise ValueError("Non integer parameter. "
                                 "Got {}".format(arg))

    def apply(self, pkt_list):
        """Keeps only the wanted packets. See `Mod.apply` for more details."""
        new_pl = PacketList()
        for i in self.sequence:
            new_pl.add_packet(pkt_list[i].pkt, pkt_list[i].delay)
        return new_pl

    def __str__(self):
        return "{name} {param}".format(
            name=self.name,
            param=" ".join(str(i) for i in self.sequence)
        )
