"""modifications
Gather all packet modifications related operations and tools.

The ModList class is used to build a list of modifications that can be applied
in order to a packet list.

The other modifications are specific operations that aims at doing one thing.
They can be inserted in a ModList.
"""
from fragscapy.modifications.mod import ModList
from fragscapy.modifications.mod_drop_one import ModDropOne
from fragscapy.modifications.mod_drop_proba import ModDropProba
from fragscapy.modifications.mod_echo import ModEcho
from fragscapy.modifications.mod_print import ModPrint

__all__ = ['ModList', 'ModDropOne', 'ModDropProba', 'ModEcho', 'ModPrint']
