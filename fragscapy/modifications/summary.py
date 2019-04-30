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

    def apply(self, pkt_list):
        """Prints the summary for each packet.See `Mod.apply` for more
        details."""
        pkt_list.summary()

        return pkt_list
