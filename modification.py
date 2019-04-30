"""modification
The modification-related objects. A modification is a transformation applied
to a list of packet. The idea is to prepare a list of packet to send, apply
some transformation and then send the modified version of the packet list.
"""
from abc import ABC, abstractmethod

class Modification(ABC):
    """Modification
    Abstract object for defining a modification of a packet list.

    Contains at least a name (default is the class name) and a documentation
    about the usage (default is a "no usage documented").
    """
    def __init__(self, name=None, doc=None):
        if name is None:
            name = self.__class__.__name__.lower()
        if doc is None:
            doc = "No usage documented".format(name=name)
        self.name = name
        self.doc = doc

    @abstractmethod
    def apply(self, pkt_list):
        """apply
        Applies the modification to a PacketList object.

        :param pkt_list: A list of packet on which the apply the modification.
        """
        pass

    def usage(self):
        """usage
        Prints the usage of the modification.
        """
        print(self.name)
        print("==========")
        print("  ", self.doc.replace('\n', '\n  '), sep='')

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.name


class ModList(list):
    """ModList
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
        """apply
        Applies the modifications to a PacketList object.

        :param pkt_list: The PacketList object to modify.
        """
        for mod in self:
            mod.apply(pkt_list)
