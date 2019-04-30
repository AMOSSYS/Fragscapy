"""mod_echo
Echo a string when this modification is applied. Does not alter the packet
list.
"""
from modification import Modification

MOD_NAME = "Echo"
MOD_DOC = "Echo a string.\necho <string>"

class ModEcho(Modification):
    """ModEcho
    Echo a string when this modification is applied. Does not alter the
    packet list.
    """
    def __init__(self, *args):
        super().__init__(MOD_NAME, MOD_DOC)
        self.string = " ".join(args)

    def apply(self, pkt_list):
        """apply
        Prints the string.

        :param pkt_list: The packet list (not used).
        """
        print(self.string)
