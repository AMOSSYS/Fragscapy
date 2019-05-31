"""Defines a list of `Mod` objects."""

class ModList(list):
    """A list modifications.

    Use the `ModList` as a classic python list, the only difference is the
    `.apply(packet_list)` method available to apply the list of modifications
    on a `PacketList` object.

    Examples:
        Assuming the all the mods and the packet list are already created:

        >>> ml = ModList()
        >>> ml.append(mod1)
        >>> ml.append(mod2)
        >>> ml.append(mod3)
        >>> len(ml)
        3
        >>> ml.pop()
        >>> ml[-1]
        mod2
        >>> ml.insert(1, mod4)
        >>> for mod in ml:
        ...     print(mod)
        mod1
        mod4
        mod2
        mod3
        >>> ml.apply(packet_list)
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
