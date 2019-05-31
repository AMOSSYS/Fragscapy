"""Abstract definition of a modification.

A modification is a transformation that can be applied to a list of packet.
The `Mod` class defines the abstract base class that should be subclassed and
concretized in order to create a new modification.
"""

import abc

class Mod(abc.ABC):
    """Abstract object for defining a modification of a packet list.

    This the base class for defining a modification. Any subclass should
    redefine the __init__ method to parse the arguments. If the class'
    attribute `_nb_args` is redefined, `Mod.__init__()` automatically
    check the number of parameters and raises a ValueError if this is not
    the right number.

    In addition, any subclass should also redefine the `.apply()` method
    to define the behavior of the mod.

    For an even better implementation one could redefine the `.name` and
    `.doc` attribute in order to get cleaner usage. But defaults are provided
    (respectively the class name and "No usage documented").

    Args:
        *args: The arguments of the mods.

    Attributes:
        name: The name of the modification.
        doc: A string that describes the goal and the syntax of the
            modification. It is displayed when requesting the usage.

    Raises:
        ValueError: incorrect number of parameters.
    """

    name = None
    doc = None
    _nb_args = -1

    @abc.abstractmethod
    def __init__(self, *args):
        if self._nb_args >= 0 and len(args) != self._nb_args:
            raise ValueError(
                "Incorrect number of parameters specified. "
                "Got {}, expected {}.".format(len(args), self._nb_args)
            )

    @abc.abstractmethod
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
