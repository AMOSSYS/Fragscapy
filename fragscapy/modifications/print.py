"""Prints the content of a packet list."""

from fragscapy.modifications.mod import Mod


class Print(Mod):
    """Prints the content of a packet list.

    Args:
        *args: The arguments of the mods.

    Raises:
        ValueError: Unrecognized or incorrect number of parameters.

    Examples:
        >>> Print()
    """

    name = "Print"
    doc = ("Prints the content of the packet list.\n"
           "print")
    _nb_args = 0

    def apply(self, pkt_list):
        """Prints the content of each packet. See `Mod.apply` for more
        details."""
        pkt_list.display()

        return pkt_list
