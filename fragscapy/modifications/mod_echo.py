"""mod_echo
Echo a string when this modification is applied. Does not alter the packet
list.
"""
from fragscapy.modifications.mod import Mod

class ModEcho(Mod):
    """ModEcho
    Echo a string when this modification is applied. Does not alter the
    packet list.
    """
    name = "Echo"
    doc = "Echo a string.\necho <string>"
    nb_args = 1

    def __init__(self, *args):
        super().__init__(*args)

        self.string = " ".join(args)

    def apply(self, pkt_list):
        """apply
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
