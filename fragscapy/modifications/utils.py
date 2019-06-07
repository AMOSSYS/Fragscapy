"""Functions and utilities that can be used by mutliple mods to avoid
duplication."""

import scapy.layers.inet6

# The IPv6 Headers that needs to be processed for routing
IPV6_PROCESS_HEADERS = ("IPv6", "IPv6ExtHdrHopByHop", "IPv6ExtHdrRouting")
# Next Header code for IPv6ExtHdrFragment
IPV6_NH_FRAG = 44


def name(layer):
    """Returns the class name of a protocol layer."""
    return layer.__class__.__name__


def fragment6(pkt, fragsize):
    """Fragment an IPv6 Scapy packet in fragments of size `fragsize`.

    `scapy.layers.inet6.fragment6` is not sufficient alone since it requires
    to already have a Fragment Extension Header in the packet (it used to
    indicate to Scapy where to split the Extension Header chain). This function
    inserts this Fragment Extension Header automatically according to the RFC
    and fragments the packets.

    Args:
        pkt: The IPv6 Scapy packet to fragment

    Returns:
        A list of fragments (IPv6 packets) of size `fragsize`.

    Examples:
        >>> fragment6(IPv6()/IPv6ExtHdrRouting()/AH()/TCP()/"PLOP"*100, 30)
    """
    return scapy.layers.inet6.fragment6(ipv6_insert_frag_hdr(pkt), fragsize)



def ipv6_get_per_frag_hdr(pkt):
    """Returns the last 'Scapy layer' of the "Per-Fragment Headers" part of
    the packet.

    The "Per-Fragment Headers" part is the chain of IPv6 headers that is
    repeated for every fragment because they are useful for routing and
    defragmenting.

    Args:
        pkt: The Scapy packet to examine.

    Returns:
        A reference to the last 'Scapy layer' of the "Per-Fragment Headers".

    Examples:
        >>> get_per_frag_hdr(IPv6()/IPv6ExtHdrRouting()/AH()/TCP()/"PLOP")
        <IPv6ExtHdrRouting  nh=AH Header |<AH  |<TCP  |<Raw  load='PLOP' |>>>>
    """
    current = pkt
    ret = current
    while current is not scapy.packet.NoPayload():
        if name(current) in IPV6_PROCESS_HEADERS:
            ret = current
        current = current.payload
    return ret


def ipv6_insert_frag_hdr(pkt):
    """Inserts a "Fragment Extension Header" in a packet just after the
    "Per-Fragment Headers" part.

    Args:
        pkt: The packet to modify.

    Returns:
        The same packet with a well-placed Fragment Extension Header.

    Examples:
        >>> insert_frag_hdr(IPv6()/IPv6ExtHdrRouting()/AH()/TCP()/"PLOP")
        <IPv6  nh=Routing Header |
          <IPv6ExtHdrRouting  nh=Fragment Header |
            <IPv6ExtHdrFragment  nh=AH Header |
              <AH |
                <TCP  |
                  <Raw  load='PLOP' |>>>>>>
    """
    current = ipv6_get_per_frag_hdr(pkt)
    current.payload = (
        scapy.layers.inet6.IPv6ExtHdrFragment(nh=current.nh)
        / current.payload
    )
    try:
        current.nh = IPV6_NH_FRAG
    except AttributeError:
        pass
    return pkt