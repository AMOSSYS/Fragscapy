"""mod_summary
Prints a 1-line summary of the packet.
"""
from fragscapy.modifications.mod import Mod

class ModSummary(Mod):
    """ModSummary
    Prints a 1-line summary of the packet.
    """
    name = "Summary"
    doc = ("Print a 1-line summary of the packet.\n"
           "summary")
    nb_args = 0

    def __init__(self, *args):
        super().__init__(*args)

    def apply(self, pkt_list):
        """apply
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
