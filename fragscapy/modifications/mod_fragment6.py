"""ModFragment6
Modification to fragment one packet. the fragmentation size must be
specified. It represents the maximum size of each packet (including
headers)
"""
from scapy.layers.inet6 import IPv6ExtHdrFragment, fragment6
from scapy.packet import NoPayload
from fragscapy.modifications.mod import Mod
from fragscapy.packet_list import PacketList


MOD_NAME = "Fragment6"
MOD_DOC = ("Fragment the IPv6 packets at the L3-layer\n"
           "fragment <size>")

PROCESS_HEADERS = ("IPv6", "IPv6ExtHdrHopByHop", "IPv6ExtHdrRouting")

def name(layer):
    """name
    Returns the class name of the object (supposed to be a protocol layer).

    :param layer: The layer to examine.
    :return: The class name of this layer.
    """
    return layer.__class__.__name__

def get_per_frag_hdr(pkt):
    """get_per_frag_hdr
    Returns the last 'Scapy layer' of the "Per-Fragment Headers" part of the
    packet.

    :param pkt: The Scapy packet to examine.
    :return: A reference to the last 'Scapy layer' of the "Per-Fragment Headers".
    """
    current = pkt
    ret = current
    while current is not NoPayload():
        if name(current) in PROCESS_HEADERS:
            ret = current
        current = current.payload
    return ret

def insert_frag_hdr(pkt):
    """insert_frag_hdr
    Insert a "Fragment Extension Header" in a packet where right after the
    "Per-Fragment Headers" and the "Extension & Upper-Layer Headers"

    :param pkt: The packet to modify
    :return: The same packet with a well-placed Fragment Extension Header
    """
    current = get_per_frag_hdr(pkt)
    current.payload = IPv6ExtHdrFragment(nh=current.nh)/current.payload
    return pkt


class ModFragment6(Mod):
    """ModFragment6
    Fragment each IPv6 packet. the fragmentation size must be specified. It
    represents the maximum size of each packet (including headers).
    """
    def __init__(self, *args):
        super().__init__(MOD_NAME, MOD_DOC)

        if len(args) != 1:
            raise ValueError("Incorrect number of parameters specified. "
                             "Got {}, expected 1".format(len(args)))

        try:
            self.fragsize = int(args[0])
        except ValueError:
            raise ValueError("Parameter 1 unrecognized. "
                             "Got {}".format(args[0]))


    def apply(self, pkt_list):
        new_pl = PacketList()

        for pkt in pkt_list:
            mod_pkt = insert_frag_hdr(pkt.pkt)
            fragments = fragment6(mod_pkt, self.fragsize)

            index = len(new_pl) - 1
            for fragment in fragments:
                new_pl.add_packet(fragment)
            new_pl.edit_delay(index, pkt.delay)

        return new_pl
