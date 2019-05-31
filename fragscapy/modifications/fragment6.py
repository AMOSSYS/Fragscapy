"""Fragments the IPv6 packets at the L3-layer."""

import scapy.layers.inet6
import scapy.packet

from fragscapy.modifications.mod import Mod
from fragscapy.packetlist import PacketList


PROCESS_HEADERS = ("IPv6", "IPv6ExtHdrHopByHop", "IPv6ExtHdrRouting")


def name(layer):
    """
    Returns the class name of the object (supposed to be a protocol layer).

    :param layer: The layer to examine.
    :return: The class name of this layer.
    """
    return layer.__class__.__name__


def get_per_frag_hdr(pkt):
    """
    Returns the last 'Scapy layer' of the "Per-Fragment Headers" part of the
    packet.

    :param pkt: The Scapy packet to examine.
    :return: A reference to the last 'Scapy layer' of the "Per-Fragment Headers".
    """
    current = pkt
    ret = current
    while current is not scapy.packet.NoPayload():
        if name(current) in PROCESS_HEADERS:
            ret = current
        current = current.payload
    return ret


def insert_frag_hdr(pkt):
    """
    Insert a "Fragment Extension Header" in a packet where right after the
    "Per-Fragment Headers" and the "Extension & Upper-Layer Headers"

    :param pkt: The packet to modify
    :return: The same packet with a well-placed Fragment Extension Header
    """
    current = get_per_frag_hdr(pkt)
    current.payload = (
        scapy.layers.inet6.IPv6ExtHdrFragment(nh=current.nh)
        / current.payload
    )
    return pkt


class Fragment6(Mod):
    """Fragments the IPv6 packets at the L3-layer.

    Fragment each IPv6 packet. the fragmentation size must be specified. It
    represents the maximum size of each packet (including headers). It uses
    the scapy's fragmentation function.

    Args:
        *args: The arguments of the mods.

    Attributes:
        fragsize: The fragmentation size (maximum length of a fragment).

    Raises:
        ValueError: Unrecognized or incorrect number of parameters.

    Examples:
        >>> Fragment6(1280).fragsize  # Minimum MTU for IPv6
        1280
    """

    name = "Fragment6"
    doc = ("Fragment the IPv6 packets at the L3-layer\n"
           "fragment <size>")
    _nb_args = 1

    def __init__(self, *args):
        super().__init__(*args)

        try:
            self.fragsize = int(args[0])
        except ValueError:
            raise ValueError("Parameter 1 unrecognized. "
                             "Got {}".format(args[0]))


    def apply(self, pkt_list):
        new_pl = PacketList()

        for pkt in pkt_list:
            mod_pkt = insert_frag_hdr(pkt.pkt)
            fragments = scapy.layers.inet6.fragment6(mod_pkt, self.fragsize)

            index = len(new_pl) - 1
            for fragment in fragments:
                new_pl.add_packet(fragment)
            new_pl.edit_delay(index, pkt.delay)

        return new_pl

    def __str__(self):
        return "{name} {param}".format(
            name=self.name,
            param=self.fragsize
        )

    def __repr__(self):
        return "{name}<fragsize: {fragsize}>".format(
            name=self.name,
            fragsize=self.fragsize
        )
