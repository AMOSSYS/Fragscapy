"""
A list of modifications used to gather some utility methods around it.
"""

class ModList(list):
    """
    A list of modifications used to gather some utility methods around it.
    """
    def __str__(self):
        ret = []
        ret.append("ModList [")
        for mod in self:
            ret.append(" - " + str(mod))
        ret.append("]")
        return "\n".join(ret)

    def __repr__(self):
        ret = []
        ret.append("ModList [")
        for mod in self:
            ret.append(" - " + repr(mod))
        ret.append("]")
        return "\n".join(ret)

    def apply(self, pkt_list):
        """
        Applies the modifications to a PacketList object.

        :param pkt_list: The PacketList object to modify.
        """
        for mod in self:
            pkt_list = mod.apply(pkt_list)
        return pkt_list
