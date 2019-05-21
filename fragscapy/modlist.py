"""
Some manipulations of the Modifications : a dedicated list for the mods to apply
and a function to dynamically import a mod.
"""
import importlib

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
            pkt_list = mod.apply(pkt_list)
        return pkt_list

def get_mod(mod_str):
    """
    Dynamically import a mod from its name using `importlib`
    """
    pkg_name = "modifications.{}".format(mod_str.lower())
    mod_name = mod_str.lower().title()
    pkg = importlib.import_module(pkg_name)
    return getattr(pkg, mod_name)
