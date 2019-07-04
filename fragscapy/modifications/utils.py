"""Functions and utilities that can be used by mutliple mods to avoid
duplication."""

import scapy.layers.inet6
import scapy.packet

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

def tcp_segment(pkt, size, overlap=None, overlap_before=False):
    """Segment a TCP packet to a certain size.

    Args:
        pkt: The packet to segment
        size: The size of the TCP data after segmentation
        overlap: A string of data at the beginning or the end that overlaps
            the other fragments
        overlap_before: Should the overlap data be added at the beginning.
            Else it is added at the end. Default is False.

    Returns:
        A list of L2-packets with TCP segments

    Examples:
        >>> tcp_segment(IP()/TCP()/"PLOP", 3)
        [
          <IP  len=None frag=0 proto=tcp chksum=None |
            <TCP  seq=0 chksum=None |
              <Raw  load='PLO' |>>>,
          <IP  len=None frag=0 proto=tcp chksum=None |
            <TCP  seq=3 chksum=None |
              <Raw  load='P' |>>>
        ]
    """

    payload = bytes(pkt.getlayer('TCP').payload)
    tcp_l = len(payload)
    if not tcp_l:  # Trivial case
        return [pkt]

    nb_segments = (tcp_l-1)//size + 1
    segments = [payload[i*size:(i+1)*size] for i in range(nb_segments)]

    ret = []
    for i, segment in enumerate(segments):
        new_pkt = pkt.copy()
        if overlap is not None:
            # Add some data that overlaps the previous/next fragment
            if overlap_before and i != 0:
                # All segments except the first one
                segment = overlap + segment
            elif not overlap_before and i == len(segments) - 1:
                # All segments except the last one
                segment = segment + overlap
        new_pkt.getlayer('TCP').payload = scapy.packet.Raw(segment)
        new_pkt.getlayer('TCP').chksum = None
        new_pkt.getlayer('TCP').seq = pkt.getlayer('TCP').seq + i*size
        if new_pkt.haslayer('IP'):
            new_pkt.getlayer('IP').len = None
            new_pkt.getlayer('IP').chksum = None
        elif new_pkt.haslayer('IPv6'):
            new_pkt.getlayer('IPv6').plen = None
            new_pkt.getlayer('IPv6').chksum = None
        ret.append(new_pkt)

    return ret
