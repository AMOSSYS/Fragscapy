"""Modifies any field of a specific layer in a packet. Only applied if the
layer and the field exists in the packet."""

import scapy.layers.all

from fragscapy.modifications.mod import Mod


class Field(Mod):
    """Modifies any field of a specific layer in a packet.

    This modification is only applied if both the required layer and the
    field exists in the packet.

    The name of the layer and the field refers to the name used by Scapy.

    Args:
        *args: The arguments of the mods.

    Attributes:
        layer_name: The name of the layer to look for.
        field_name: The name of the field to look for.
        randval: The volatile random object used by Scapy.
        value: The new value to insert. None if random.

    Raises:
        ValueError: Unrecognized or incorrect number of parameters.

    Examples:
        >>> TcpSport(1234).sport
        1234
    """

    name = "Field"
    doc = ("Modifies any field of a specific layer in a packet.\n"
           "field <layer> <field> {random|<fixed_sport>}")
    _nb_args = 3

    def parse_args(self, *args):
        """See base class."""
        self.layer_name = args[0]
        self.field_name = args[1]

        layer_class = getattr(scapy.layers.all, self.layer_name)
        fieldtype = layer_class().fieldtype[self.field_name]
        self.randval = fieldtype.randval()

        self._random = False
        if args[2] == "random":
            self._random = True
            self.value = None  # Exact value will be calculated later
        else:
            self.value = args[2]
            try:
                if (self.value > self.randval.max
                        or self.value < self.randval.min):
                    raise ValueError(
                        "Parameter 3 must be beetween {} and {}. Got {}"
                        .format(self.randval.min, self.randval.max, self.value)
                    )
            except TypeError:
                # self.value cannot be compared
                pass

    def is_deterministic(self):
        """See base class."""
        return not self._random

    def apply(self, pkt_list):
        """Modifies any field of a specific layer in a packet. See `Mod.apply`
        for more details."""
        value = self.value
        if self._random:
            value = self.randval._fix()  # pylint: disable=protected-access

        for pkt in pkt_list:
            if pkt.pkt.haslayer(self.layer_name):
                layer = pkt.pkt.getlayer(self.layer_name)
                try:
                    layer.setfieldval(self.field_name, value)
                except AttributeError:
                    pass  # The field name does not exists

        return pkt_list

    def get_params(self):
        """See base class."""
        return {
            'layer_name': self.layer_name,
            'field_name': self.field_name,
            'value': self.value if not self._random else "random",
        }
