"""mod_echo
Echo a string when this modification is applied. Does not alter the packet
list.
"""
from fragscapy.modifications.mod import Mod

MOD_NAME = "Echo"
MOD_DOC = "Echo a string.\necho <string>"

class ModEcho(Mod):
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
