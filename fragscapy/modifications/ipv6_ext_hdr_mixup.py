"""Mixes-up the order of the IPv6 Extension Header of an IPv6 packet."""

import random

import scapy.packet

from fragscapy.modifications.mod import Mod


IPV6_EXTHDR = (
    "IPv6ExtHdrHopByHop", "IPv6ExtHdrRouting", "IPv6ExtHdrFragment", "ESP",
    "AH", "MobileIP", "IPv6ExtDestOpt")


def name(layer):
    """Returns the class name of a protocol layer."""
    return layer.__class__.__name__


def slice_exthdr(pkt):
    """Slices the packet in three parts:
    * the 'before the Extension Headers' part
    * the chain of 'Extension Headers' as a list
    * the 'after the Extension Headers' part

    Args:
        pkt: The packet to slice.

    Returns:
        A 3-tuple with the 3 parts described above. The parts no longer
        contains the other parts. It means, for instance, that the 'before'
        part's payload is `NoPayload()` and is not linked to the 'Extension
        Headers' nor the 'after' part anymore.

    Examples:
        >>> slice_exthdr(IPv6()/IPv6ExtHdrRouting()/AH()/TCP()/"PLOP")
        (<IPv6  nh=Routing Header |<IPv6ExtHdrRouting  |>>,
         [<IPv6ExtHdrRouting  |>, <AH  |>],
         <TCP  |<Raw  load='PLOP' |>>)
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
    """Rebuilds a packet from the three parts as in `slice_exthdr`.

    It does not return the packet but instead modifies it directly.
    This avoiding having the need to pass a reference to the first
    layer.

    Args:
        before: The 'before the Extension Headers' part.
        exthdr: The new chain of 'Extension Headers'.
        after: The 'after the Extension Headers' part.

    Examples:
        >>> pkt = IPv6()/IPv6ExtHdrRouting()
        >>> replace_exthdr(
        ...     pkt,
        ...     [IPv6ExtHdrRouting(), AH()],
        ...     TCP()/"PLOP"
        ... )
        >>> pkt
        <IPv6  nh=Routing Header |
          <IPv6ExtHdrRouting  nh=AH Header |
            <AH  |
              <TCP  |
                <Raw  load='PLOP' |>>>>>
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

    def is_deterministic(self):
        """See base class."""
        return False

    def apply(self, pkt_list):
        """Mixes-up the order of the Extension Headers for each IPv6 packet.
        See `Mod.apply` for more info."""
        for pkt in pkt_list:
            before, chain, after = slice_exthdr(pkt.pkt)
            random.shuffle(chain)
            replace_exthdr(before, chain, after)

        return pkt_list
