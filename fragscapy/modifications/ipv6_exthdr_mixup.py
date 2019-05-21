"""
Randomly changes the order to the Extension Headers of the IPv6 packet
"""
from random import shuffle
from scapy.packet import NoPayload
from .mod import Mod

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
    before = NoPayload()
    chain = []
    while current.payload is not NoPayload():
        if name(current.payload) in IPV6_EXTHDR:
            if not chain:
                # If this is the first Extension Header, store the 'before'
                before = current
            chain.append(current.payload)
        current = current.payload
    # The 'after' is the payload of the last Extension Header
    after = chain[-1].payload if chain else NoPayload()

    # Removes the dependency between the Headers
    for hdr in chain:
        hdr.payload = NoPayload()

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

class IPv6ExtHdrMixup(Mod):
    """
    Randomly changes the order to the Extension Headers of the IPv6 packet
    """
    name = "IPv6ExtHdrMixup"
    doc = ("Mixup the order of the extension headers in an IPv6 packet\n"
           "ipv6_exthdr_mixup")
    nb_args = 0

    def __init__(self, *args):
        super().__init__(*args)

    def apply(self, pkt_list):
        """apply
        Randomly changes the order of the Extension Headers of each packet.

        :param pkt_list: The packet list
        """
        for pkt in pkt_list:
            before, chain, after = slice_exthdr(pkt.pkt)
            shuffle(chain)
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
