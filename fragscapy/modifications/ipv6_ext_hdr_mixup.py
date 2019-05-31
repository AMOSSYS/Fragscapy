"""Mixes-up the order of the IPv6 Extension Header of an IPv6 packet."""

import random

import scapy.packet

from fragscapy.modifications.mod import Mod


IPV6_EXTHDR = (
    "IPv6ExtHdrHopByHop", "IPv6ExtHdrRouting", "IPv6ExtHdrFragment", "ESP",
    "AH", "MobileIP", "IPv6ExtDestOpt")


def name(layer):
    """
    Returns the class name of the object (supposed to be a protocol layer).

    :param layer: The layer to examine.
    :return: The class name of this layer.
    """
    return layer.__class__.__name__


def slice_exthdr(pkt):
    """
    Cuts the packet in three:
    * the 'before the Extension Headers' part
    * the chain of 'Extension Headers' as a list
    * the 'after the Extension Headers' part

    :param pkt: The packet to slice.
    :return: A 3-tuple with the 3 parts described above.
    """
    current = pkt
    before = scapy.packet.NoPayload()
    chain = []
    while current.payload is not scapy.packet.NoPayload():
        if name(current.payload) in IPV6_EXTHDR:
            if not chain:
                # If this is the first Extension Header, store the 'before'
                before = current
            chain.append(current.payload)
        current = current.payload
    # The 'after' is the payload of the last Extension Header
    after = chain[-1].payload if chain else scapy.packet.NoPayload()

    # Removes the dependency between the Headers
    for hdr in chain:
        hdr.payload = scapy.packet.NoPayload()

    return before, chain, after


def replace_exthdr(before, exthdr, after):
    """
    Takes a chain of Extension Headers and link them together in the given
    order. Then inserts this new chain in the packet 'in-place'.

    :param before: The 'before the Extension Headers' part
    :param exthdr: The new chain of 'Extension Headers'
    :param after: The 'after the Extension Headers' part
    """
    if not exthdr:
        return

    new_chain = exthdr[0]
    current = new_chain
    i = 1
    while i < len(exthdr):
        current.payload = exthdr[i]
        i += 1
        current = current.payload

    # Add the 'before' before the new chain of Extension Headers
    before.payload = new_chain
    # Add the 'after' after the last Extension Header
    current.payload = after


class Ipv6ExtHdrMixup(Mod):
    """Mixes-up the order of the extension headers in an IPv6 packet.

    Randomly changes the order to the Extension Headers of the IPv6 packet

    Args:
        *args: The arguments of the mods.

    Raises:
        ValueError: Unrecognized or incorrect number of parameters.

    Examples:
        >>> Ipv6ExtHdrMixup()
    """

    name = "Ipv6ExtHdrMixup"
    doc = ("Mixes-up the order of the extension headers in an IPv6 packet\n"
           "ipv6_ext_hdr_mixup")
    _nb_args = 0

    def __init__(self, *args):
        super().__init__(*args)

    def apply(self, pkt_list):
        """apply
        Randomly changes the order of the Extension Headers of each packet.

        :param pkt_list: The packet list
        """
        for pkt in pkt_list:
            before, chain, after = slice_exthdr(pkt.pkt)
            random.shuffle(chain)
            replace_exthdr(before, chain, after)

        return pkt_list

    def __str__(self):
        return "{name}".format(
            name=self.name
        )

    def __repr__(self):
        return "{name}<>".format(
            name=self.name
        )
