"""Print the content of a packet list."""

from fragscapy.modifications.mod import Mod


class Print(Mod):
    """
    Print the content of a packet list.
    """
    name = "Print"
    doc = ("Print the content of the packet list.\n"
           "print")
    nb_args = 0

    def __init__(self, *args):
        super().__init__(*args)

    def apply(self, pkt_list):
        """
        For each packet in the packet list, displays its content.

        :param pkt_list: The packet list.
        """
        pkt_list.display()

        return pkt_list

    def __str__(self):
        return "{name}".format(
            name=self.name
        )

    def __repr__(self):
        return "{name}<>".format(
            name=self.name
        )
