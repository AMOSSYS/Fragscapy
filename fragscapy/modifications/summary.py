"""Prints a 1-line summary of the packet."""

from fragscapy.modifications.mod import Mod


class Summary(Mod):
    """Prints a 1-line summary of the packet.

    Args:
        *args: The arguments of the mods.

    Raises:
        ValueError: Unrecognized or incorrect number of parameters.

    Examples:
        >>> Summary()
    """

    name = "Summary"
    doc = ("Prints a 1-line summary of the packet.\n"
           "summary")
    _nb_args = 0

    def __init__(self, *args):
        super().__init__(*args)

    def apply(self, pkt_list):
        """
        For each packet in the packet list, show the summary

        :param pkt_list: The packet list.
        """
        pkt_list.summary()

        return pkt_list

    def __str__(self):
        return "{name}".format(
            name=self.name
        )

    def __repr__(self):
        return "{name}<>".format(
            name=self.name
        )
