"""http
Performs all the requests necessary for a standard GET HTTP IPv6 request and
returns the server response.
"""
from random import randint
from scapy.layers.inet6 import IPv6
from scapy.layers.inet import TCP
from scapy.packet import Raw
from scapy.sendrecv import sniff
from fragscapy.modifications.mod import ModList
from fragscapy.packet_list import PacketList

TCP_A_FLAG = 0b00010000

class HTTP6:
    """HTTP6
    Performs all the requests necessary for a standard GET HTTP IPv6 request
    and returns the server response.

    :param hostname: The hostame or IPv6 of the server
    :param modlist: A modification list to apply(default: None i.e.
        no modifications)
    :param dport: The destination port (default: 80)
    """
    def __init__(self, hostname, modlist=None, dport=80):
        self.hostname = hostname
        self.http_host = "localhost"
        self.dport = dport
        self.sport = randint(1025, 0xffff)
        if modlist is None:
            modlist = ModList()
        self.modlist = modlist

        self.state = 0
        self.seq = 0
        self.ack = 0

    def send(self, payload):
        """send
        Apply all the standard modification to the packet so it will go to the
        right destination and apply the modification list and finally send the
        packets

        :param payload: The data to send. Can be Raw, TCP or IPv6
        """
        if isinstance(payload, str):
            payload = Raw(payload.encode())
        if not payload.haslayer('TCP'):
            payload = TCP(flags='A')/payload
        if not payload.haslayer('IPv6'):
            payload = IPv6()/payload
        payload['TCP'].sport = self.sport
        payload['TCP'].dport = self.dport
        payload['TCP'].seq = self.seq
        if TCP_A_FLAG & payload['TCP'].flags:
            payload['TCP'].ack = self.ack
        payload['IPv6'].dst = self.hostname

        packet_list = PacketList()
        packet_list.add_packet(payload)
        packet_list = self.modlist.apply(packet_list)
        packet_list.send_all()

    def sniff(self, count=1):
        """sniff
        Sniff the packets on the network for a maximum of 10 seconds and
        returns the results.

        :param count: The number of packet match before stopping. `0` for
            no limit. (Default: 1)
        """
        http_filter = "ip6 and src {ip} and src port {sport} and dst port {dport}".format(
            ip=self.hostname, sport=self.dport, dport=self.sport)
        replies = sniff(filter=http_filter, timeout=10, count=count)
        return replies

    def three_way_handshake(self):
        """three_way_handshake
        Performs the TCP three-way handshake if the connexion is not
        established.
        """
        if self.state == 0:
            self.send(TCP(flags='S'))
            synack = self.sniff()
            if synack:
                self.state = 1
                self.seq = synack[0]['TCP'].ack
                self.ack = synack[0]['TCP'].seq + 1
                self.send(TCP(flags='A'))

    def reset(self):
        """reset
        Performs the TCP reset (RST) if the connexion is established
        """
        if self.state == 1:
            self.send(TCP(flags='R'))

    def get(self, path='/'):
        """get
        Performs a GET HTTP request to a given path. Handles the three-way
        hanshake and reset automatically.

        :param path: The URL path to query (default: '/')
        :return: A list of HTTP payload responses.
        """
        ret = []
        self.three_way_handshake()
        if self.state == 1:
            get = "GET {path} HTTP/1.1\r\nHost: {http_host}\r\n\r\n".format(
                path=path, http_host=self.http_host)
            self.send(get)
            replies = self.sniff()
            if replies:
                for reply in replies:
                    if reply.haslayer('TCP'):
                        if reply.haslayer('Raw'):
                            ret.append(reply['Raw'].load.decode())
                        self.seq = reply['TCP'].ack
                        self.ack = reply['TCP'].seq + 1
                        self.send(TCP(flags='A'))
                    else:
                        print("Missing TCP layer.")
            else:
                print("No replies from server")
            self.reset()
        else:
            print("Unable to do the trhee-way handshake")
        return ret


if __name__ == '__main__':
    ip_dst = input("IPv6 dest [fd02::1]: ") or "fd02::1"
    url_path = input("URL Path [/]: ") or "/"
    for data in HTTP6(ip_dst).get(url_path):
        print(data)
