"""Abstract definition of a modification.

A modification is a transformation that can be applied to a list of packet.
The `Mod` class defines the abstract base class that should be subclassed and
concretized in order to create a new modification.
"""

from abc import ABC, abstractmethod

class Mod(ABC):
    """
    Abstract object for defining a modification of a packet list.

    Contains at least a name (default is the class name) and a documentation
    about the usage (default is a "no usage documented").
    """
    name = None
    doc = None
    nb_args = -1

    @abstractmethod
    def __init__(self, *args):
        if self.nb_args >= 0 and len(args) != self.nb_args:
            raise ValueError(
                "Incorrect number of parameters specified. "
                "Got {}, expected {}.".format(len(args), self.nb_args)
            )

    @abstractmethod
    def apply(self, pkt_list):
        """
        Applies the modification to a PacketList object. It returns a
        PacketList object but might also modified the original. Actually
        the returned object might even be the same "in-memory" original
        object. There is no guarantee, the pkt_list will not be modified.
        It depends on the implementation of the modification.

        :param pkt_list: A list of packet on which to apply the modifications.
        :return: The new PacketList object resulting from the modfications.
        """
        pass

    @classmethod
    def usage(cls):
        """
        Prints the usage of the modification.
        """
        if cls.name is None:
            print(cls.__class__.__name__.lower())
        else:
            print(cls.name)
        print("==========")
        if cls.doc is None:
            print("No usage documented")
        else:
            print("  ", cls.doc.replace('\n', '\n  '), sep='')

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.name
