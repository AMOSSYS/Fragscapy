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

    def __init__(self, *args):
        self.check_args(*args)
        self.parse_args(*args)

    def is_deterministic(self):  # pylint: disable=no-self-use
        """Is the modification deterministic (no random)."""
        return True

    def parse_args(self, *args):
        """Parses the arguments and extract the necessary data from it.

        Args:
            *args: The argument received

        Raises:
            ValueError: At least one of the argument cannot be parsed.
        """

    def check_args(self, *args):
        """Performs some checks on the arguments.

        Base class only check that the number of arguments is equal to
        `self._nb_args`.

        Args:
            *args: The arguments received.

        Raises:
            ValueError: The arguments are not correct.
        """
        if self._nb_args >= 0 and len(args) != self._nb_args:
            raise ValueError(
                "Incorrect number of parameters specified. "
                "Got {}, expected {}.".format(len(args), self._nb_args)
            )

    @abc.abstractmethod
    def apply(self, pkt_list):
        """Applies the modification to a list of packets.

        It always returns a `PacketList` object but might also modified the
        original. Actually the returned object might even be the same
        "in-memory" original object. There is no guarantee that `pkt_list`
        will not be modified. It depends on the implementation of the
        modification.

        Args:
            pkt_list: A `PacketList` on which to apply the modifications.

        Returns:
            The new `PacketList` object resulting from the modfications.
        """
        raise NotImplementedError

    @classmethod
    def usage(cls):
        """Prints the usage of the modification based on the `name` and `doc`
        attributes."""
        if cls.name is None:
            print(cls.__class__.__name__.lower())
        else:
            print(cls.name)
        print("==========")
        if cls.doc is None:
            print("No usage documented")
        else:
            print("  ", cls.doc.replace('\n', '\n  '), sep='')

    def get_params(self):
        """Returns a dictionnary of the options defining the mod."""
        return {k: v for k, v in vars(self).items() if k[0] != "_"}

    def __str__(self):
        params = " ".join(str(v) for v in self.get_params().values())
        if params:
            return "{name} {params}".format(name=self.name, params=params)
        return "{name}".format(name=self.name)

    def __repr__(self):
        return "{name}<{params}>".format(
            name=self.name,
            params=", ".join("{}={}".format(k, v)
                             for k, v in self.get_params().items())
        )
