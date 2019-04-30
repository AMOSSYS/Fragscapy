"""Echoes a string."""

from fragscapy.modifications.mod import Mod

class Echo(Mod):
    """Echoes a string.

    This modification neither alter the packet nor depend on it. It simply
    prints the string that was passed as a parameter.

    Args:
        *args: The arguments of the mods.

    Attributes:
        string: The string that will be echoed

    Examples:
        >>> Echo("Hello, world!").string
        Hello, world!
        >>> Echo("plop", "i", "plop").string
        plop i plop
    """

    name = "Echo"
    doc = "Echo a string.\necho <string>"

    def parse_args(self, *args):
        """See base class."""
        self.string = " ".join(args)

    def apply(self, pkt_list):
        """Print the string. See `Mod.apply` for more details."""
        print(self.string)

        return pkt_list
