"""
Groups the different objects used to manipulate the NFQueue packets in userland.

NFQUEUE is a special Netfilter target that can be used to send packet to
userland and modify them before sending them. To access them, this module uses
`fnfqueue` module (which makes use of libnfqueue).

Here it can be used to capture traffic (with an optional filter on protocol, host
and/or port) and cast them to Scapy packets so they can be manipulated. Once the
python modification is done, one would simply invoke the `.mangle()` or `.drop()`
methods to notify Netfilter of either a new packet or the want to drop the packet.
So far, the only L3-protocols supported are IPv4 and IPv6. Other protocols are not
yet supported and those packets and accepted without being sent to the user.

The main objects to use are `NFQueueRule` which is used to manipulate iptables and
ip6tables rules and `NFQueue`, the queue that can be iterated over to access the
packets in the NFQUEUE target.
"""

import subprocess
from collections import namedtuple
from abc import ABC, abstractmethod
import fnfqueue
from scapy.data import ETH_P_IP, ETH_P_IPV6
from scapy.layers.inet import IP as scapy_IP
from scapy.layers.inet6 import IPv6 as scapy_IPv6
from scapy.sendrecv import send as scapy_send

from .utils import check_root

# Define a constant structure that holds the options for iptables together
Chain = namedtuple('Chain', ['name', 'host_opt', 'port_opt', 'qnum'])
OUTPUT = Chain('OUTPUT', '-d', '--dport', 0)
INPUT = Chain('INPUT', '-s', '--sport', 1)

class NFQueueRule:
    """
    Manipulates the iptables and ip6tables to make use of the NFQUEUE for the
    packets that are to be routed through python. It is used to insert and
    remove the correct iptables/ip6tables rules with the correct optional
    filters that configure netfilter to send the matching packets to the
    NFQUEUE target.

    >>> # Prepare the rules with the correct filter
    >>> http_alt_rule = NFQueueRule(host="www.lmddgtfy.com", port=8080)
    >>> http_rule = NFQueueRule(host="www.lmddgtfy.com", port=80)
    >>> # Insert those rules
    >>> http_alt_rule.insert()
    >>> http_rule.insert()
    >>> # Remove the rules when finished
    >>> http_alt_rule.remove()
    >>> http_rule.remove()

    :param output_chain: Apply the rule on the output chain if True. Default
        is True.
    :param input_chain: Apply the rule on the input chain if True. Default
        is True.
    :param proto: The protocol name (iptables-style) to filter on. If set to
        None and `port` is set, defaults to 'tcp', else defaults to None and
        all protocols will match.
    :param host: The hostname or IPv4 to filter on. Default is None, which
        means all hosts will match.
    :param host6: The IPv6 to filter on. Default is None. If `host` is also
        set to None, all hosts (IPv4 and IPv6) will match, else, if `host`
        is set to a hostname, the same hostname is used for IPv6 (iptables
        resolves once and for all to IPv4 and IPv6 when the rules are created)
    :param port: The TCP/UDP port to filter on. If sets to None, which is the
        default, all ports will match.
    :param ipv4: Enable IPv4. Default is True
    :param ipv6: Enable IPv6. Default is True
    :param qnum: the Queue number for the NFQUEUE target. Default is 0. To
        respect, how this modules uses NFQUEUE, it should be even : qnum is
        used for OUTPUT and qnum+1 is used for INPUT. If qnum is odd, a
        `ValueError` is raised.
    """
    def __init__(self, output_chain=True, input_chain=True, proto=None,
                 host=None, host6=None, port=None, ipv4=True, ipv6=True,
                 qnum=0):
        if not output_chain and not input_chain:
            raise ValueError("Can not deactivate both output_chain and "
                             "input_chain")

        if not ipv4 and not ipv6:
            raise ValueError("Can not deactivate both IPv4 and IPv6")

        if qnum % 2:
            raise ValueError("qnum should be even")

        if proto is None and port is not None:
            # proto default to 'tcp' when only the port is specified
            proto = 'tcp'
        if host6 is None:
            # host6 default to the same as host if not specified
            host6 = host

        self.output_chain = output_chain
        self.input_chain = input_chain
        self.proto = proto
        self.host = host if ipv4 else None
        self.host6 = host6 if ipv6 else None
        self.port = port if proto.lower() in ('tcp', 'udp') else None
        self.ipv4 = ipv4
        self.ipv6 = ipv6
        self.qnum = qnum

    def _build_filter(self, chain, h):
        opt = []    # A list of iptables options
        opt.append(chain.name)                   # OUTPUT or INPUT
        if h is not None:
            opt.append(chain.host_opt)           # -d or -s
            opt.append(h)                        # <hostname>
        if self.proto is not None:
            opt.append('-p')                     # -p
            opt.append(self.proto)               # <protocol>
            if self.port is not None:
                opt.append(chain.port_opt)       # --dport or --sport
                opt.append(str(self.port))       # <port>
        return opt

    def _build_nfqueue_opt(self, chain):
        opt = []
        opt.append('-j')                         # -j
        opt.append('NFQUEUE')                    # NFQUEUE
        opt.append('--queue-num')                # --queue-num
        opt.append(str(self.qnum + chain.qnum))  # <qnum> or <qnum>+1
        return opt

    def _build_rst_opt(_self, _):
        opt = []
        opt.append("--tcp-flags")
        opt.append("RST")
        opt.append("RST")
        opt.append("-j")
        opt.append("DROP")
        return opt

    @check_root
    def _insert_or_remove(self, insert=True):
        bin_host = []
        if self.ipv4:
            bin_host.append(("/sbin/iptables", self.host))
        if self.ipv6:
            bin_host.append(("/sbin/ip6tables", self.host6))

        chains = []
        if self.output_chain:
            chains.append(OUTPUT)
        if self.input_chain:
            chains.append(INPUT)


        for binary, h in bin_host:
            for chain in chains:
                for opt_func in (self._build_nfqueue_opt,
                                 self._build_rst_opt):
                    # Build the iptables/ip6tables resulting command
                    cmd = []
                    cmd.append(binary)
                    if insert:
                        cmd.append('-I')
                    else:
                        cmd.append('-D')
                    cmd.extend(self._build_filter(chain, h))
                    cmd.extend(opt_func(chain))
                    # Run the command and raise an exception if an error occurs
                    subprocess.run(cmd, check=True)

    def insert(self):
        """
        Build and insert the resulting rules in iptables and ip6tables.
        A `subprocess.CalledProcessError` exception is raised if an error
        occurs in the process.
        """
        self._insert_or_remove(insert=True)

    def remove(self):
        """
        Remove the previously inserted rules in iptables and ip6tables.
        A `subprocess.CalledProcessError` exception is raised if an error
        occurs in the process.
        """
        self._insert_or_remove(insert=False)




class NFQueue:
    """
    Queue object that contains the different packets in the NFQUEUE target.
    It can be iterated over in a for-loop to access them one by one or call
    the `next_packet()` method to access only one packet. The packets are
    either `fragscapy.nf_queue.IP` objects or `fragscapy.nf_queue.IPv6`
    objects, depending on the `ethertype` parameters received from Layer-2.

    Here is an example of how to setup a proxy from port 8080 to port 80
    (see `fragscapy.nf_queue.IP` documentation for how to use the packets):

    >>> q = NFQueue()
    >>> for p in q:
    ...     if p.haslayer('TCP'):
    ...         t = p.getlayer('TCP')
    ...         print("{}:{} -> ".format(t.sport, t.dport), end='')
    ...         if t.sport == 80:
    ...             t.sport = 8080
    ...         if t.dport == 8080:
    ...             t.dport = 80
    ...         t.chksum = None
    ...         print("{}:{}".format(t.sport, t.dport))
    ...     p.mangle()

    :param qnum: The queue number to use. For the same reasons explained in
        `NFQueue`'s documentations, qnum should be even and will raise a
        `ValueError` exception if not.
    """
    def __init__(self, qnum=0):
        if qnum % 2:
            raise ValueError('qnum should be even')

        self._conn = fnfqueue.Connection()
        self._conn.bind(qnum).set_mode(fnfqueue.MAX_PAYLOAD, fnfqueue.COPY_PACKET)
        self._conn.bind(qnum+1).set_mode(fnfqueue.MAX_PAYLOAD, fnfqueue.COPY_PACKET)

    def __iter__(self):
        return self

    def __next__(self):
        return self.next_packet()

    def next_packet(self):
        """
        Returns only one packet from the queue.
        """
        for p in self._conn:
            if p.hw_protocol == ETH_P_IP:
                return IP(p)
            if p.hw_protocol == ETH_P_IPV6:
                return IPv6(p)
            p.accept()
        return None


class _PacketWrapper(ABC):
    """
    A Scapy representation of the data received from the NFQUEUE target.
    In depth, it is the junction of a `scapy` IP (or IPv6) packet and a
    `fnfqueue` packet so both modules can be used : the `scapy` methods
    are available the same way as for a scapy packet but the method to
    validate (or drop) the `fnfqueue` packets are still usable.
    See the corresponding documentation to learn how to use those modules.

    :param pkt: the `fnfqueue` packet received
    :param output: Is the packet from the OUTPUT chain. Default is True
    """

    def __init__(self, pkt):
        self._scapy_pkt = self.l3_layer(pkt.payload)
        self._fnfqueue_pkt = pkt
        self._output = pkt.packet.queue_id % 2 == 0

    @property
    @abstractmethod
    def l3_layer(self):
        """
        The `scapy` l3-layer constructor to use (e.g. `scapy.layers.inet.IP`
        or `scapy.layers.inet6.IPv6`)
        """
        raise NotImplementedError

    @property
    def is_input(self):
        """ True is the packet comes from INPUT chain """
        return not self._output

    @property
    def is_output(self):
        """ True if the packet comes from OUTPUT chain """
        return self._output

    def _apply_modifications(self):
        self._fnfqueue_pkt.payload = bytes(self._scapy_pkt)

    def __dir__(self):

        ret = ['_scapy_pkt', '_fnfqueue_pkt', 'l3_layer', 'is_input',
               'is_output']
        ret.extend(dir(self._scapy_pkt))
        ret.extend(dir(self._fnfqueue_pkt))
        return ret

    def __getattr__(self, name):
        try:
            return getattr(self._scapy_pkt, name)
        except AttributeError:
            pass
        ret = getattr(self._fnfqueue_pkt, name)
        # When accessing the underlying fnfqueue methods,
        # force to apply the modifications (useful before calling methods
        # such as accept, mangle, verdict, ...)
        self._apply_modifications()
        return ret

    def raw_send(self):
        """
        Send the scapy packet directly on a raw socket. The charge of dropping
        the nfqueued packed is left to the user (if necessary).
        """
        scapy_send(self._scapy_pkt)



class IP(_PacketWrapper):
    """ See _PacketWrapper documentation """
    l3_layer = scapy_IP
    __doc__ = _PacketWrapper.__doc__


class IPv6(_PacketWrapper):
    """ See _PacketWrapper documentation """
    l3_layer = scapy_IPv6
    __doc__ = _PacketWrapper.__doc__
