"""ModFragment6
Modification to fragment one packet. the fragmentation size must be
specified. It represents the maximum size of each packet (including
headers)
"""
from random import randint
from scapy.layers.inet6 import IPv6ExtHdrFragment
from scapy.packet import NoPayload
from fragscapy.modifications.mod import Mod
from fragscapy.packet_list import PacketList


MOD_NAME = "Fragment6"
MOD_DOC = ("Fragment the IPv6 packets at the L3-layer\n"
           "fragment <size>")

FRAG_NH = 44
IPV6_EXT_HEADERS = ("IPv6ExtHdrHopByHop", "IPv6ExtHdrRouting",
                    "IPv6ExtHdrFragment", "IPv6ExtHdrDestOpt")
UNFRAG_HEADERS = ("IPv6ExtHdrHopByHop", "IPv6ExtHdrRouting")

def name(layer):
    """name
    Returns the class name of the object (supposed to be a protocol layer).

    :param layer: The layer to examine.
    :return: The class name of this layer.
    """
    return layer.__class__.__name__

def get_per_frag_hdr(pkt):
    """get_per_frag_hdr
    Returns the "Per-Fragment Headers" part of the packet i.e. the headers
    that must be repeated for each packet.

    :param pkt: The Scpay packet to examine.
    :return: A tuple of two references pointing to the first and the last
        Scapy layer of the "Per-Fragment Headers".
    """
    begin = pkt
    end = pkt
    while name(end.payload) in UNFRAG_HEADERS:
        end = end.payload
    return begin, end

def get_ext_upper_layer_hdr(per_frag_hdr_end):
    """get_ext_upper_layer_hdr
    Returns the "Extension & Upper-Layer Headers" part of the packet i.e. the
    part that must be in the first fragment.

    :param per_frag_hdr_end: A reference to the last Scapy layer of the
        "Per-Fragment Headers".
    :return: A 3-tuple with
        * The value of 'Next Header' field in the last Extension Header (the
        one to use in the Fragmentation Header),
        * A reference pointing to the first Scpay layer of the "Extension &
        Upper-Layer Headers",
        * A reference pointing to the last Scpay layer of the "Extension &
        Upper-Layer Headers".
    """
    begin = per_frag_hdr_end.payload
    end = per_frag_hdr_end.payload
    frag_nh = per_frag_hdr_end.nh
    while name(end) in IPV6_EXT_HEADERS:
        frag_nh = end.nh
        end = end.payload
    return frag_nh, begin, end

def get_first_fragment(pkt, frag_id, frag_nh, frag_data, frag_m=False):
    """get_first_fragment
    Build the first fragment (slightly different than the others) of a
    fragmented packet.

    :param pkt: The packet to fragment.
    :param frag_id: The fragmentation 'Identification' field's value to use.
    :param frag_nh: The fragmentation 'Next Header' field's value to use.
    :param frag_data: The raw data to insert in the first fragment.
    :param frag_m: The fragmentation 'M' field's value to use. i.e. is there
        more fragments after this one ? (default: False)
    :return: The first fragment of a fragmented packet.
    """
    # Copy the packet as a reference
    new_pkt = pkt.copy()
    # Retrieve the "Per-Fragment Headers"
    new_pfh_begin, new_pfh_end = get_per_frag_hdr(new_pkt)
    # Retrieve the "Extension & Upper-Layer Headers"
    _, new_eulh_begin, new_eulh_end = get_ext_upper_layer_hdr(new_pfh_end)

    # Remove the payload after new_pfh_end so new_pfh_begin only contains
    # the Per-Fragment Headers
    new_pfh_end.payload = NoPayload()
    new_pfh_end.nh = FRAG_NH
    # Remove the payload after new_eulh_end so new_eulh_begin only contains
    # the Extension & Upper-Layer Headers
    new_eulh_end.payload = NoPayload()
    # Build the first fragment from calculated headers
    new_fragment = (
        new_pfh_begin
        / IPv6ExtHdrFragment(nh=frag_nh, id=frag_id, m=frag_m, offset=0)
        / new_eulh_begin
        / frag_data
    )
    return new_fragment

def get_other_fragment(pkt, frag_id, frag_nh, frag_data, frag_m=False, frag_offset=0):
    """get_other_fragment
    Build one of the other (non-first) fragments of a fragmented packet.

    :param pkt: The packet to fragment.
    :param frag_id: The fragmentation 'Identification' field's value to use.
    :param frag_nh: The fragmentation 'Next Header' field's value to use.
    :param frag_data: The raw data to insert in the first fragment.
    :param frag_m: The fragmentation 'M' field's value to use. i.e. is there
        more fragments after this one ? (default: False)
    :param frag_offset: The fragmentation 'Offset' field's value to use.
    :return: One fragment of a fragmented packet with the frag_data.
    """
    # Copy the old packet as a reference
    new_pkt = pkt.copy()
    # Retrieve the "Per-Fragment Headers"
    new_pfh_begin, new_pfh_end = get_per_frag_hdr(new_pkt)

    # Remove the other headers and data
    new_pfh_end.payload = NoPayload()
    new_pfh_end.nh = FRAG_NH
    # Assemble the new fragment
    new_fragment = (
        new_pfh_begin
        / IPv6ExtHdrFragment(nh=frag_nh, id=frag_id, m=frag_m, offset=frag_offset)
        / frag_data
    )
    return new_fragment

def get_fragments(pkt, size, frag_id):
    """get_fragments
    Fragments a packet in multiple valid packets of maximum `size` bytes.

    :param pkt: The packet to fragment.
    :param size: The maximum size of a fragment.
    :param frag_id: The fragmentation 'Identification' field's value to use.

    :return: A list of Scapy packets that corresponds to the different fragments.
    """
    # Calculate the differente parts of the packet
    _, per_frag_hdr_end = get_per_frag_hdr(pkt)
    tmp_infos = get_ext_upper_layer_hdr(per_frag_hdr_end)
    frag_nh, ext_upper_layer_hdr_begin, ext_upper_layer_hdr_end = tmp_infos
    frag_part = ext_upper_layer_hdr_end.payload

    # Since this part will be in the first packet, the first packet must be at
    # least bigger
    if len(pkt) - len(frag_part) > size:
        raise ValueError("Fragmentation size too small. Must be above {} at "
                         "least".format(len(pkt) - len(frag_part)))

    # The raw data to split
    frag_dump = frag_part.build()
    # The list of fragments to populate
    fragments = []
    # An index to mesure where are the beginning and the end of the next frag
    i, j = 0, 0

    # The data that can be inserted in the first fragment
    data_size = size - (len(pkt) - len(frag_part))
    data_size = data_size - data_size%8  # Make sure it is a multiple of 8
    j = i + data_size
    frag_data = frag_dump[i:j]

    # The first fragment is special as it contains ext_upper_layer_hdr
    fragments.append(get_first_fragment(
        pkt, frag_id, frag_nh, frag_data, frag_m=j<len(frag_dump)
    ))

    # consider the data as read
    i = j

    # Then build all other fragments in a similar way
    while j < len(frag_dump):
        # The current fragment data
        data_size = size - (len(pkt) - len(ext_upper_layer_hdr_begin))
        data_size = data_size - data_size%8  # Make sure it is a multiple of 8
        j = i + data_size
        frag_data = frag_dump[i:j]

        fragments.append(get_other_fragment(
            pkt, frag_id, frag_nh, frag_data, frag_m=j<len(frag_dump), frag_offset=i//8
        ))

        # Consider the data as read
        i = j

    return fragments


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
        frag_id_init = randint(0, 0xffffffff)
        for pkt in pkt_list:
            frag_id_init = (frag_id_init + 1)%0xffffffff
            try:
                fragments = get_fragments(pkt.pkt, self.fragsize, frag_id_init)
            except ValueError as e:
                print(e, "Passing the modification")
                new_pl.add_packet(pkt.pkt, pkt.delay)
                continue
            index = len(new_pl) - 1
            for fragment in fragments:
                new_pl.add_packet(fragment)
            new_pl.edit_delay(index, pkt.delay)
        return new_pl
