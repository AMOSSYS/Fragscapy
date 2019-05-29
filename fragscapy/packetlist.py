"""A list of wrappers around Scapy packets and metadata (e.g. delay)."""

import time
from scapy.sendrecv import send as scapy_send
from scapy.sendrecv import sendp as scapy_sendp

# The minimum time (in seconds) a packet will be delayed
MIN_TIME_DELAY = 0.01

def _safe_delay(delay):
    """
    Checks that a delay is a positive float number.

    :param delay: The delay expression to check.
    :return:      The sanitized delay as a float.
    """
    try:
        delay = float(delay)
    except ValueError:
        print("Please specify a correct delay")
        raise ValueError("{} is not a valid delay (not a number)".format(delay))
    if delay < 0:
        print("Please specify a correct delay")
        raise ValueError("{} is not a valid delay (not positive)".format(delay))
    return delay


class PacketStruct:
    """
    A structure to hold the underlying Scapy packet along with a delay to wait
    before sending the packet.
    """
    def __init__(self, pkt, delay):
        self._pkt = pkt
        self._delay = _safe_delay(delay)

    @property
    def pkt(self):
        """
        The underlying Scapy packet.
        """
        return self._pkt

    @pkt.setter
    def pkt(self, val):
        self._pkt = val

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
        if self._delay > MIN_TIME_DELAY:
            time.sleep(self._delay)
        scapy_send(self._pkt)

    def sendp(self):
        """
        Sends the packet as a Layer3 packet.
        """
        # Only sleep if above the min limit
        if self._delay > MIN_TIME_DELAY:
            time.sleep(self._delay)
        scapy_sendp(self._pkt)

    def display(self):
        """
        Displays the delay (if any) followed by the details of the underlying
        Scapy packet.
        """
        if self._delay > MIN_TIME_DELAY:
            print("Delay of {} seconds".format(self._delay))
        self._pkt.display()

    def copy(self):
        """
        Make a copy of the PacketStruct object

        :return: A new and different PacketStruct object with the same data
        """
        return PacketStruct(self._pkt, self._delay)

    def __str__(self):
        ret = []
        if self._delay > MIN_TIME_DELAY:
            ret.append("{}s".format(self._delay))
        ret.append(str(self._pkt))
        return "\n".join(ret)

    def __repr__(self):
        ret = []
        if self._delay > MIN_TIME_DELAY:
            ret.append("{}s".format(self._delay))
        ret.append(repr(self._pkt))
        return "\n".join(ret)



class PacketList:
    """
    Representation of a list of packet to send.

    This list can be altered (edit, append, insert, remove) before being
    really sent. For each packet a delay can be specified. This delay will
    be respected and waited before actually sending the packet.
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

    def __repr__(self):
        ret = []
        ret.append("PacketList [")
        for pkt in self.pkts:
            ret.append(repr(pkt))
        ret.append("]")
        return "\n".join(ret)
