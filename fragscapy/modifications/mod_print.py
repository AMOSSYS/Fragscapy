"""mod_print
Print the content of a packet list.
"""
from fragscapy.modifications.mod import Mod

MOD_NAME = "Print"
MOD_DOC = "Print the content of the packet list.\nprint"

class ModPrint(Mod):
    """ModPrint
    Print the content of a packet list.
    """
    def __init__(self, *_):
        super().__init__(MOD_NAME, MOD_DOC)

    def apply(self, pkt_list):
        """apply
        For each packet in the packet list, displays its content.

        :param pkt_list: The packet list.
        """
        pkt_list.display()

        return pkt_list
