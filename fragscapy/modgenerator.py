"""Generator for modifications and modifications lists.

The objects in this module are generator used to generate the `Mod`
and the `ModList` based on precise parametrization.

The `ModOption`-derived classes are used to generates 1 option (e.g. an
integer, a string, ...) based on a type of option (e.g. a sequence, a range,
...).

The  `ModGenerator` contains multiple `ModOption`s and generates 1 `Mod`
object by enumerating all the different combination of options.

The `ModListGenerator` contains multiple `ModGenerator`s and generates 1
`ModList` object by enumerating all the different combination of mods.
"""

import importlib
import os
from abc import ABC, abstractmethod
from inflection import camelize, underscore

from .modlist import ModList

# Package where the modifications are stored (and loaded from)
MOD_PACKAGE = 'fragscapy.modifications'
# Directory where the modifications are stored
MOD_DIR = 'modifications'


class ModGeneratorError(ValueError):
    """ Error with the mods generation. """
    pass


class ModOption(ABC):
    """
    Abstract class of a single option generator in a mod (i.e. 1 of the
    parameter passed to the constructor of the mod). It should implement a
    `.get_option(i)` and a `.nb_options()` methods. It can then be used to
    generate 1 instance of the option (based on the parameter given on init).

    It can be used as a generator or as list-like object.

    >>> for opt in mod_option:  # Used in for-loops
    ...     print(opt)
    >>> n = len(mod_option)     # Size = number of different instances
    >>> opt = mod_option[n-1]   # Retrieve last instance

    :param mod_name: the name of this modification (used only for errors
        messages).
    :param opt_name: the name of this option of this modification (used only
        for errors messages).
    """
    def __init__(self, mod_name, opt_name):
        self.opt_name = opt_name
        self.mod_name = mod_name

    @abstractmethod
    def get_option(self, i):
        """
        Calculate the i-th instance of the option. The result must be
        deterministic, constant for a given `i`. E.g. asking for
        `.get_option(10)` must always output the same result.

        The `ModOption.get_option` method implements the checks for 0<i<len
        so any subclass of `ModOption` should begin with a call to
        `super().get_option(i)` for consistency.

        :param i: the number of the configuration.
        """
        if (not isinstance(i, int)
                or i < 0
                or i >= self.nb_options()):
            self._raise_error(
                "'i' should be between 0 and {}, got '{}'".format(
                    self.nb_options()-1, i
                )
            )

    @abstractmethod
    def nb_options(self):
        """
        Calculates the number of possible options for this generator.
        """
        pass

    def _raise_error(self, msg):
        """
        Raises a `ModGeneratorError` alogn with indication of the option and
        the name of the mod.

        :param msg: A message explaining the error.
        """
        raise ModGeneratorError("Error with option '{}' of mod '{}': {}".format(
            self.opt_name, self.mod_name, msg))

    def __len__(self):
        return self.nb_options()

    def __getitem__(self, i):
        return self.get_option(i)

    def __iter__(self):
        return (self.get_option(i) for i in range(self.nb_options()))

    def __str__(self):
        return "{}".format(self.opt_name)

    def __repr__(self):
        return "{}".format(self.__class__.__name__)


class ModOptionRange(ModOption):
    """
    A modification option generator for range of integer. It's behavior is
    the same as the built-in python function `range`.
    The argument is a list of 1, 2 or 3 integers (positives or negatives are
    supported). If 1 integer is passed, the range goes from 0 to arg[0] with a
    step of 1. If 2 integers are passed, the range goes from arg[0] to arg[1]
    with a step of 1. If 3 integers are passed, the range goes from arg[0] to
    arg[1] with a step of arg[2].

    >>> list(ModOptionRange("foo", [1]))
    [0, 1]
    >>> list(ModOptionRange("foo", [5,8]))
    [5, 6, 7, 8]
    >>> list(ModOptionRange("foo", [-10,-1]))
    [-10, -9, -8, -7, -6, -5, -4, -3, -2, -1]
    >>> list(ModOptionRange("foo", [-10,-1, 3]))
    [-10, -7, -4, -1]

    :param mod_name: The name of the mod (used only for error messages).
    :param args: The list of arguments to parametrize the generator.
    """
    def __init__(self, mod_name, args):
        super(ModOptionRange, self).__init__(mod_name, "range")

        # Parsing of options
        self.start = 0
        self.stop = None
        self.step = 1
        if not args:
            self._raise_error("Too few arguments, got none")
        elif len(args) == 1:
            self.stop = self._int(args, 0)
        elif len(args) == 2:
            self.start = self._int(args, 0)
            self.stop = self._int(args, 1)
        elif len(args) == 3:
            self.start = self._int(args, 0)
            self.stop = self._int(args, 1)
            self.step = self._int(args, 2)
        else:
            self._raise_error("Too much arguments, got '{}'".format(args))

        # Checking validity of options
        if self.step == 0:
            self._raise_error("'step' can't be 0")
        if self.step > 0 and self.start > self.stop:
            self._raise_error(
                "'start' ('{}') can't be bigger than 'stop' ('{}')".format(
                    self.start, self.stop
                )
            )
        if self.step < 0 and self.start < self.stop:
            self._raise_error(
                "'start' ('{}') can't be smaller than 'stop' ('{}')".format(
                    self.start, self.stop
                )
            )

    def _int(self, l, i):
        """ Small function to cast the i-th value of l to an integer. """
        try:
            return int(l[i])
        except ValueError:
            self._raise_error(
                "Can't cast argument n°{} to int, got '{}'".format(i, l[0])
            )

    def get_option(self, i):
        """
        Calculate the i-th instance of the generation.
        See `ModOption.get_option` for more info.
        """
        super(ModOptionRange, self).get_option(i)
        return self.start + self.step * i

    def nb_options(self):
        """
        Calculate the i-th instance of the generation.
        See `ModOption.nb_options` for more info.
        """
        return (self.stop - self.start)//self.step + 1

    def __str__(self):
        return "range {} {} {}".format(self.start, self.stop, self.step)

    def __repr__(self):
        return "ModOptionRange({}, [{}, {}, {}])".format(
            self.mod_name, self.start, self.stop, self.step
        )


class ModOptionSequenceStr(ModOption):
    """
    A modification option generator for a sequence of strings.
    The argument is a list of strings which will be the different
    values used in the same order.

    >>> list(ModOptionSequenceStr("foo", ["a", "b", "c", "d"]))
    ['a', 'b', 'c', 'd']

    :param mod_name: The name of the mod (used only for error messages).
    :param args: The list of arguments to parametrize the generator.
    """
    def __init__(self, mod_name, args):
        super(ModOptionSequenceStr, self).__init__(mod_name, "seq_str")

        # Verify there is at least 1 element
        if not args:
            self._raise_error("No string in sequence")

        self.seq = args

    def get_option(self, i):
        """
        Calculate the i-th instance of the generation.
        See `ModOption.get_option` for more info.
        """
        super(ModOptionSequenceStr, self).get_option(i)
        return self.seq[i]

    def nb_options(self):
        """
        Calculate number of instances of the generation.
        See `ModOption.nb_options` for more info.
        """
        return len(self.seq)

    def __str__(self):
        return "seq_str {}".format(" ".join(self.seq))

    def __repr__(self):
        return "ModOptionSequenceStr({}, {})".format(self.mod_name, self.seq)


class ModOptionSequenceInt(ModOption):
    """
    A modification option generator for a sequence of integers.
    The argument is a list of integers which will be the different
    values used in the same order.

    >>> list(ModOptionSequenceInt("foo", [1, 10, 2, 20, 3, 30]))
    [1, 10, 2, 20, 3, 30]

    :param mod_name: The name of the mod (used only for error messages).
    :param args: The list of arguments to parametrize the generator.
    """
    def __init__(self, mod_name, args):
        super(ModOptionSequenceInt, self).__init__(mod_name, "seq_int")

        # Verify there is at least 1 element
        if not args:
            self._raise_error("No number in sequence")

        self.seq = list()
        for arg in args:
            try:
                self.seq.append(int(arg))
            except ValueError:
                self._raise_error("Non-int argument, got '{}'".format(arg))

    def get_option(self, i):
        """
        Calculate the i-th instance of the generation.
        See `ModOption.get_option` for more info.
        """
        super(ModOptionSequenceInt, self).get_option(i)
        return self.seq[i]

    def nb_options(self):
        """
        Calculate the number of instances of the generation.
        See `ModOption.nb_options` for more info.
        """
        return len(self.seq)

    def __str__(self):
        return "seq_int {}".format(" ".join(str(n) for n in self.seq))

    def __repr__(self):
        return "ModOptionSequenceInt({}, {})".format(self.mod_name, self.seq)


class ModOptionSequenceFloat(ModOption):
    """
    A modification option generator for a sequence of floats.
    The argument is a list of floats which will be the different
    values used in the same order.

    >>> list(ModOptionSequenceFloat("foo", [1, 10.5, 2.4, 20, 3, 30.48]))
    [1.0, 10.5, 2.4, 20, 3, 30.48]

    :param mod_name: The name of the mod (used only for error messages).
    :param args: The list of arguments to parametrize the generator.
    """
    def __init__(self, mod_name, args):
        super(ModOptionSequenceFloat, self).__init__(mod_name, "seq_float")

        # Verify there is at least 1 element
        if not args:
            self._raise_error("No number in sequence")

        self.seq = list()
        for arg in args:
            try:
                self.seq.append(float(arg))
            except ValueError:
                self._raise_error("Non-float argument, got '{}'".format(arg))

    def get_option(self, i):
        """
        Calculate the i-th instance of the generation.
        See `ModOption.get_option` for more info.
        """
        super(ModOptionSequenceFloat, self).get_option(i)
        return self.seq[i]

    def nb_options(self):
        """
        Calculate the number of instances of the generation.
        See `ModOption.nb_options` for more info.
        """
        return len(self.seq)

    def __str__(self):
        return "seq_float {}".format(" ".join(str(n) for n in self.seq))

    def __repr__(self):
        return "ModOptionSequenceFloat({}, {})".format(self.mod_name, self.seq)


class ModOptionStr(ModOption):
    """
    A modification option generator that generate only 1 option which is a
    string.
    The args is a list (for consistency with other mod options) with a single
    element: the string.

    >>> list(ModOptionStr("foo", ["bar"]))
    ["bar"]

    :param mod_name: The name of the mod (used only for error messages).
    :param args: The list of arguments to parametrize the generator.
    """
    def __init__(self, mod_name, args):
        super(ModOptionStr, self).__init__(mod_name, "str")

        # Verify there is exactly 1 argument
        if len(args) != 1:
            self._raise_error(
                "There should be only 1 element, got '{}'".format(args)
            )

        self.s = args[0]

    def get_option(self, i):
        """
        Returns the string, i.e. the only instance possible.
        See `ModOption.get_option` for more info.
        """
        super(ModOptionStr, self).get_option(i)
        return self.s

    def nb_options(self):
        """
        Returns always 1 because there is ony 1 instance possible.
        See `ModOption.nb_options` for more info.
        """
        return 1

    def __str__(self):
        return "str {}".format(self.s)

    def __repr__(self):
        return "ModOptionStr({}, [{}])".format(self.mod_name, self.s)


class ModOptionInt(ModOption):
    """
    A modification option generator that generate only 1 option which is an
    integer.
    The args is a list (for consistency with other mod options) with a single
    element: the integer.

    >>> list(ModOptionInt("foo", [18]))
    [18]

    :param mod_name: The name of the mod (used only for error messages).
    :param args: The list of arguments to parametrize the generator.
    """
    def __init__(self, mod_name, args):
        super(ModOptionInt, self).__init__(mod_name, "int")

        # Verify there is exactly 1 argument
        if len(args) != 1:
            self._raise_error(
                "There should be only 1 element, got '{}'".format(args)
            )

        try:
            self.n = int(args[0])
        except ValueError:
            self._raise_error("Can't cast '{}' to an integer".format(args[0]))

    def get_option(self, i):
        """
        Returns the integer, i.e. the only instance possible.
        See `ModOption.get_option` for more info.
        """
        super(ModOptionInt, self).get_option(i)
        return self.n

    def nb_options(self):
        """
        Returns always 1 because there is ony 1 instance possible.
        See `ModOption.nb_options` for more info.
        """
        return 1

    def __str__(self):
        return "int {}".format(self.n)

    def __repr__(self):
        return "ModOptionInt({}, [{}])".format(self.mod_name, self.n)


class ModOptionFloat(ModOption):
    """
    A modification option generator that generate only 1 option which is a
    floating decimal number.
    The args is a list (for consistency with other mod options) with a single
    element: the float.

    >>> list(ModOptionFloat("foo", [18]))
    [18.0]
    >>> list(ModOptionFloat("foo", [42.58]))
    [42.58]

    :param mod_name: The name of the mod (used only for error messages).
    :param args: The list of arguments to parametrize the generator.
    """
    def __init__(self, mod_name, args):
        super(ModOptionFloat, self).__init__(mod_name, "float")

        # Verify there is exactly 1 argument
        if len(args) != 1:
            self._raise_error(
                "There should be only 1 element, got '{}'".format(args)
            )

        try:
            self.n = float(args[0])
        except ValueError:
            self._raise_error("Can't cast '{}' to a float".format(args[0]))

    def get_option(self, i):
        """
        Returns the float, i.e. the only instance possible.
        See `ModOption.get_option` for more info.
        """
        super(ModOptionFloat, self).get_option(i)
        return self.n

    def nb_options(self):
        """
        Returns always 1 because there is ony 1 instance possible.
        See `ModOption.nb_options` for more info.
        """
        return 1

    def __str__(self):
        return "float {}".format(self.n)

    def __repr__(self):
        return "ModOptionFloat({}, [{}])".format(self.mod_name, self.n)


class ModGenerator:
    """
    A generator for a modification. For dynamic and evolution purposes, the
    `Mod` object is imported based on the `mod_name` given. It can then be
    used to generate all the possible mods with all the possible combinations
    for the options, as described in mod_opts.

    It can be used as a generator or as list-like object.

    >>> for mod in ModGenerator("echo", ["seq_str foo bar"]):
    ...     print(repr(mod))
    Echo<string: foo>
    Echo<string: bar>
    >>> print(ModGenerator("fragment6", ["range 1280 6000 50"])[50])
    Fragment6 3780
    >>> len(ModGenerator("select", [0, 2, "seq_int 3 4 5", "range 7 20"]))
    42

    :param mod_name: The name of the modification (for importing the correct
        mod and improve error messages).
    :param mod_opts: A list with the options to use to build `ModOption`s
        objects.
    """
    def __init__(self, mod_name, mod_opts):
        self.mod_name = mod_name
        self.mod = get_mod(mod_name)

        self.mod_opts = list()
        for opt in mod_opts:
            # Find the right ModOption or default to Str or Int
            if isinstance(opt, str):
                opt_args = opt.split()
                opt_type = opt_args[0]
                if opt_type == "range":
                    self.mod_opts.append(ModOptionRange(mod_name, opt_args[1:]))
                elif opt_type == "seq_str":
                    self.mod_opts.append(ModOptionSequenceStr(mod_name, opt_args[1:]))
                elif opt_type == "seq_int":
                    self.mod_opts.append(ModOptionSequenceInt(mod_name, opt_args[1:]))
                elif opt_type == "seq_float":
                    self.mod_opts.append(ModOptionSequenceFloat(mod_name, opt_args[1:]))
                elif opt_type == "str":
                    self.mod_opts.append(ModOptionStr(mod_name, opt_args[1:]))
                elif opt_type == "int":
                    self.mod_opts.append(ModOptionInt(mod_name, opt_args[1:]))
                elif opt_type == "float":
                    self.mod_opts.append(ModOptionFloat(mod_name, opt_args[1:]))
                else:  # By default consider it as a string
                    self.mod_opts.append(ModOptionStr(mod_name, [opt]))
            else:  # By default consider it as an int
                self.mod_opts.append(ModOptionInt(mod_name, [opt]))


    def get_mod(self, i):
        """
        Calculate the i-th instance of the mod. The result must be
        deterministic, constant for a given `i`. E.g. asking for
        `.get_mod(10)` must always output the same result.

        :param i: the number of the configuration.
        """
        if (not isinstance(i, int)
                or i < 0
                or i >= self.nb_mods()):
            raise ModGeneratorError(
                "Error with mod '{}': 'i' should be between 0 and {}, got '{}'"
                .format(self.mod_name, self.nb_mods()-1, i)
            )
        opts = list()
        for opt in self.mod_opts:
            opts.append(opt[i % len(opt)])
            i -= i % len(opt)
            i //= len(opt)
        return self.mod(*opts)

    def nb_mods(self):
        """
        The number of different mods possible. It is basically the
        multiplication of the length of the different ModOption it is
        composed of.
        """
        ret = 1
        for opt in self.mod_opts:
            ret *= len(opt)
        return ret

    def __getitem__(self, i):
        return self.get_mod(i)

    def __len__(self):
        return self.nb_mods()

    def __iter__(self):
        return (self.get_mod(i) for i in range(self.nb_mods()))

    def __str__(self):
        return (
            "{{ \n"
            "  \"mod_name\": \"{}\",\n"
            "  \"mod_opts\": [{}]\n"
            "}}"
        ).format(
            self.mod_name,
            ", ".join("\""+str(opt)+"\"" for opt in self.mod_opts)
        )

    def __repr__(self):
        return "ModGenerator({}, opts=[{}])".format(
            self.mod_name,
            ", ".join(opt.opt_name for opt in self.mod_opts)
        )


class ModListGenerator:
    """
    A generator for a `ModList`. The modlist is created based on the
    specifications for each of its mods as it come from the `Config` object.

    It simply creates a `ModGenerator` for each of the defined mod, store
    them and use them to generate 1 modlist instance (i.e. A ModList with
    1 mod instance from the ModGenerator for each mod).

    >>> modlist_gen = ModListGenerator([
    ...     {"mod_name": "fragment6", "mod_opts": ["seq_str 1280 1500 1800"]},
    ...     {"mod_name": "echo", "mod_opts": ["seq_str foo bar fuz ball"]},
    ...     {"mod_name": "select", "mod_opts": [1, 2, 3, 4, 5]}
    ... ])
    >>> print(repr(modlist_gen))
    ModListGenerator(mods=[fragment6, echo, select])
    >>> len(modlist_gen)
    12
    >>> modlist_gen[5]
    ModList [
     - Fragment6<fragsize: 1800>
     - Echo<string: bar>
     - Select<sequence: [1, 2, 3, 4, 5]>
    ]

    :param mods: A list of mods where each element is a dictionary containing
        the key 'mod_name' with the name of the mod and the key 'mod_opts'
        with the list of options to use to build the ModGenerator.
    """
    def __init__(self, mods):
        self.mod_generators = list()
        for mod in mods:
            self.mod_generators.append(
                ModGenerator(mod['mod_name'], mod['mod_opts'])
            )

    def get_modlist(self, i):
        """
        Calculate the i-th instance of the modlist. The result must be
        deterministic, constant for a given `i`. E.g. asking for
        `.get_modlist(10)` must always output the same result.

        :param i: the number of the configuration.
        """
        if (not isinstance(i, int)
                or i < 0
                or i >= self.nb_modlists()):
            raise ModGeneratorError(
                "'i' should be between 0 and {}, got '{}'"
                .format(self.nb_modlists()-1, i)
            )
        modlist = ModList()
        for mod_generator in self.mod_generators:
            modlist.append(mod_generator[i % len(mod_generator)])
            i -= i % len(mod_generator)
            i //= len(mod_generator)
        return modlist

    def nb_modlists(self):
        """
        The number of different modlists possible. It is basically the
        multiplication of the length of the different ModGenerator it is
        composed of.
        """
        ret = 1
        for mod_generator in self.mod_generators:
            ret *= len(mod_generator)
        return ret

    def __getitem__(self, i):
        return self.get_modlist(i)

    def __len__(self):
        return self.nb_modlists()

    def __iter__(self):
        return (self.get_modlist(i) for i in range(self.nb_modlists()))

    def __str__(self):
        return "[\n  {}\n]".format(
            ",\n  ".join(str(mod_gen).replace('\n', '\n  ')
                         for mod_gen in self.mod_generators)
        )

    def __repr__(self):
        return "ModListGenerator(mods=[{}])".format(
            ", ".join(mod_gen.mod_name for mod_gen in self.mod_generators)
        )


def get_all_mods():
    """
    Retrieve all the available mods using `importlib` and `os.listdir`.
    """
    dirname = os.path.dirname(__file__)
    all_mods = list()
    for mod_name in os.listdir(os.path.join(dirname, MOD_DIR)):
        if not mod_name.endswith('.py'):
            continue
        if mod_name in ('__init__.py', 'mod.py'):
            continue
        mod_name = mod_name[:-3]
        all_mods.append(get_mod(mod_name))

    return all_mods


def get_mod(mod_name):
    """
    Dynamically import a mod from its name using `importlib`.
    """
    pkg_name = "{}.{}".format(MOD_PACKAGE, underscore(mod_name))
    mod_name = camelize(mod_name)

    pkg = importlib.import_module(pkg_name)
    return getattr(pkg, mod_name)
