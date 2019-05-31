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

    def __init__(self, *args):
        super().__init__(*args)

        self.string = " ".join(args)

    def apply(self, pkt_list):
        """
        Prints the string.

        :param pkt_list: The packet list (not used).
        """
        print(self.string)

        return pkt_list

    def __str__(self):
        return "{name} {param}".format(
            name=self.name,
            param=self.string
        )

    def __repr__(self):
        return "{name}<string: {string}>".format(
            name=self.name,
            string=self.string
        )
