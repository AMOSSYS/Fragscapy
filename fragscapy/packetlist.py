"""A list of wrappers around Scapy packets and metadata (e.g. delay)."""

import time

import scapy.sendrecv


# The minimum time (in seconds) a packet will be delayed
MIN_TIME_DELAY = 0.01


def _safe_delay(delay):
    """Checks that `delay` is a positive float number else raises a
    ValueError."""
    try:
        delay = float(delay)
    except ValueError:
        raise ValueError("{} is not a valid delay (not a number)".format(delay))
    if delay < 0:
        raise ValueError("{} is not a valid delay (not positive)".format(delay))
    return delay


class PacketStruct(object):
    """Wrapper around a Scapy packet and a delay.

    The delay is used when sending the Scapy packet, it is delayed by the same
    amount of seconds. That way, the user can easily control the delay between
    each packet to be sent.

    Args:
        pkt: The Scapy packet.
        delay: The delay (in seconds) before sending the packet.

    Attributes:
        pkt: The Scapy packet.

    Examples:
        >>> pkt = PacketStruct(IP()/TCP()/"PLOP", 25)
        >>> pkt.display()
        Delay of 25.0 seconds
        ###[ IP ]###
          version   = 4
          [...]
        ###[ TCP ]###
             sport     = ftp_data
             [...]
        ###[ Raw ]###
                load      = 'PLOP'
        >>> print(repr(pkt))
        PacketStruct(pkt=44B, delay=25.0s)
    """
    def __init__(self, pkt, delay):
        self.pkt = pkt
        self._delay = _safe_delay(delay)

    @property
    def delay(self):
        """
        The delay to wait before sending the packet.
        """
        return self._delay

    @delay.setter
    def delay(self, val):
        self._delay = _safe_delay(val)

    def send(self):
        """
        Sends the packet as a Layer2 packet.
        """
        # Only sleep if above the min limit
        if self.delay > MIN_TIME_DELAY:
            time.sleep(self.delay)
        scapy.sendrecv.send(self.pkt)

    def sendp(self):
        """
        Sends the packet as a Layer3 packet.
        """
        # Only sleep if above the min limit
        if self.delay > MIN_TIME_DELAY:
            time.sleep(self.delay)
        scapy.sendrecv.sendp(self.pkt)

    def display(self):
        """
        Displays the delay (if any) followed by the details of the underlying
        Scapy packet.
        """
        if self.delay > MIN_TIME_DELAY:
            print("Delay of {} seconds".format(self.delay))
        self.pkt.display()

    def copy(self):
        """
        Make a copy of the PacketStruct object

        :return: A new and different PacketStruct object with the same data
        """
        return PacketStruct(self.pkt, self.delay)

    def __str__(self):
        ret = []
        if self.delay > MIN_TIME_DELAY:
            ret.append(str(self.delay) + "s")
        ret.append(str(self.pkt))
        return "\n".join(ret)

    def __bytes__(self):
        ret = []
        if self.delay > MIN_TIME_DELAY:
            ret.append(bytes(str(self.delay), encoding='ascii') + b"s")
        ret.append(bytes(self.pkt))
        return b"\n".join(ret)

    def __repr__(self):
        return "PacketStruct(pkt={}B, delay={}s)".format(
            len(self.pkt), self.delay
        )


class PacketList(object):
    """A list of PacketStruct to be sent.

    This list can be altered (edit, append, insert, remove) before being
    really sent. For each packet a delay can be specified. This delay will
    be respected and waited before actually sending the packet.

    Attributes:
        pkts: The list of packets

    Examples:
        >>> pl = PacketList()
        >>> pl.add_packet(IP()/TCP()/"PLOP", 25)
        >>> pl.add_packet(IP()/TCP()/"PLIP", 2)
        >>> pl.display()
        Delay of 25.0 seconds
        ###[ IP ]###
          version   = 4
          [...]
        ###[ TCP ]###
             sport     = ftp_data
             [...]
        ###[ Raw ]###
                load      = 'PLOP'
        Delay of 2.0 seconds
        ###[ IP ]###
          version   = 4
          [...]
        ###[ TCP ]###
             sport     = ftp_data
             [...]
        ###[ Raw ]###
                load      = 'PLIP'
        >>> repr(pl)
        'PacketList(pkts=[PacketStruct(pkt=44B, delay=25.0s),
                          PacketStruct(pkt=44B, delay=2.0s)])'
    """
    def __init__(self):
        self.pkts = []

    def __getitem__(self, index):
        return self.pkts[index]

    def __len__(self):
        return len(self.pkts)

    def __iter__(self):
        return iter(self.pkts)

    def add_packet(self, pkt, delay=0):
        """
        Adds a new Scapy packet at the end of the list.

        :param pkt:   The Scapy packet to add.
        :param delay: The delay to respect before packet emission (default: 0).
        """
        self.pkts.append(PacketStruct(pkt, delay))

    def edit_delay(self, index, delay):
        """
        Changes the delay before packet emission.

        :param index: Position of the packet to change.
        :param delay: The new delay.
        """
        self.pkts[index].delay = delay

    def edit_packet(self, index, pkt):
        """
        Changes the underlying Scapy packet.

        :param index: Position of the packet to change.
        :param pkt:   The new Scapy packet.
        """
        self.pkts[index].pkt = pkt

    def remove_packet(self, index):
        """
        Removes a packet from the list.

        :param index: Position of the packet to remove.
        """
        del self.pkts[index]

    def insert_packet(self, index, pkt, delay=0):
        """
        Inserts a new packet in the list at the given index.

        :param index: Position to insert the new packet.
        :param pkt:   The new packet itself.
        :param delay: Delay to respect before sending packet. (default: 0)
        """
        self.pkts.insert(index, PacketStruct(pkt, delay))

    def send_all(self):
        """
        Sends all packets in the list as Layer3 packets.
        """
        for pkt in self.pkts:
            pkt.send()

    def sendp_all(self):
        """
        Sends all packets in the list as Layer2 packets.
        """
        for pkt in self.pkts:
            pkt.sendp()

    def display(self):
        """
        Displays the details of each packet of the packet list.
        """
        for pkt in self.pkts:
            pkt.display()

    def __str__(self):
        ret = []
        ret.append("PacketList [")
        for pkt in self.pkts:
            ret.append(str(pkt))
        ret.append("]")
        return "\n".join(ret)

    def __bytes__(self):
        ret = []
        ret.append(b"PacketList [")
        for pkt in self.pkts:
            ret.append(bytes(pkt))
        ret.append(b"]")
        return b"\n".join(ret)

    def __repr__(self):
        return "PacketList(pkts=[{}])".format(
            ', '.join(repr(pkt) for pkt in self.pkts)
        )
