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
from fragscapy.modifications.mod_duplicate import ModDuplicate
from fragscapy.modifications.mod_reorder import ModReorder
from fragscapy.modifications.mod_select import ModSelect
from fragscapy.modifications.mod_fragment6 import ModFragment6
from fragscapy.modifications.mod_ipv6_exthdr_mixup import ModIPv6ExtHdrMixup
from fragscapy.modifications.mod_ipv6_hop import ModIPv6Hop
from fragscapy.modifications.mod_ipv6_length import ModIPv6Length
from fragscapy.modifications.mod_ipv6_nh import ModIPv6NH

__all__ = ['ModList', 'ModDropOne', 'ModDropProba', 'ModEcho', 'ModPrint',
           'ModDuplicate', 'ModReorder', 'ModSelect', 'ModFragment6',
           'ModIPv6ExtHdrMixup', 'ModIPv6Hop', 'ModIPv6Length', 'ModIPv6NH']
