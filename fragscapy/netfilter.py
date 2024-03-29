"""Netfilter-related manipulations (i.e. NF rules and packets in NFQUEUE).

NFQUEUE is a special Netfilter target that can be used to send packet to
userland and modify them before sending them. To access them, this module uses
`fnfqueue` module (which makes use of libnfqueue).

Here it can be used to capture traffic (with an optional filter on protocol,
host and/or port) and cast them to Scapy packets so they can be manipulated.
Once the python modification is done, one would simply invoke the `.mangle()`
or `.drop()` methods to notify Netfilter of either a new packet or the want to
drop the packet. So far, the only L3-protocols supported are IPv4 and IPv6.
Other protocols are not yet supported and those packets and accepted without
being sent to the user.

The main objects to use are `NFQueueRule` which is used to manipulate iptables
and ip6tables rules and `NFQueue`, the queue that can be iterated over to
access the packets in the NFQUEUE target.
"""

import abc
import collections
import os
import subprocess

import fnfqueue

import scapy.data
import scapy.layers.inet
import scapy.layers.inet6
import scapy.sendrecv


# Define a constant structure that holds the options for iptables together
Chain = collections.namedtuple('Chain',
                               ['name', 'host_opt', 'port_opt', 'qnum'])
OUTPUT = Chain('OUTPUT', '-d', '--dport', 0)
INPUT = Chain('INPUT', '-s', '--sport', 1)


class NFQueueRule(object):  # pylint: disable=too-many-instance-attributes
    """A Netfilter rule to enable/disable the NFQUEUE.

    Manipulates the iptables and ip6tables to make use of the NFQUEUE for the
    packets that are to be routed through python. It is used to insert and
    remove the correct iptables/ip6tables rules with the correct optional
    filters that configure netfilter to send the matching packets to the
    NFQUEUE target.

    Args:
        output_chain: Apply the rule on the output chain if 'True'. Default is
            'True'.
        input_chain: Apply the rule on the input chain if 'True'. Default is
            'True'.
        proto: The protocol name (iptables-style) to filter on. If set to
            'None' and `port` is set, defaults to 'tcp', else defaults to
            'None' and all protocols will match.
        host: The hostname or IPv4 to filter on. Default is 'None', which
            means all hosts will match.
        host6: The IPv6 to filter on. Default is 'None'. If `host` is also set
            to 'None', all hosts (IPv4 and IPv6) will match, else, if `host`
            is set to a hostname, the same hostname is used for IPv6 (iptables
            resolves once and for all to IPv4 and IPv6 when the rules are
            created).
        port: The TCP/UDP port to filter on. If sets to 'None', which is the
            default, all ports will match.
        ipv4: Enable IPv4 if 'True'. Default is 'True'.
        ipv6: Enable IPv6 if 'True'. Default is 'True'.
        qnum: The Queue number for the NFQUEUE target. Default is '0'. To
            respect, how this modules uses NFQUEUE, it should be even: qnum is
            used for OUTPUT and qnum+1 is used for INPUT. If qnum is odd, a
            `ValueError` is raised.

    Attributes:
        output_chain: Apply the rule on the output chain if 'True'.
        input_chain: Apply the rule on the input chain if 'True'.
        proto: The protocol name (iptables-style) to filter on. 'None' means
            all proto will match.
        host: The hostname or IPv4 to filter on. 'None' means all hosts will
            match.
        host6: The IPv6 to filter on. 'None' means all hosts will match.
        port: The TCP/UDP port to filter on. 'None' means all ports will
            match.
        ipv4: Enable IPv4 if 'True'.
        ipv6: Enable IPv6 if 'True'.
        qnum: The Queue number for the NFQUEUE target.

    Raises:
        ValueError: See the message for details. Wrong combination of
            parameters.

    Examples:
        >>> # Prepare the rules with the correct filter
        >>> http_alt_rule = NFQueueRule(
        ...     input_chain=False, host="www.lmddgtfy.com", port=8080)
        >>> http_rule = NFQueueRule(
        ...     output_chain=False, host="www.lmddgtfy.com", port=80)
        >>> # Insert those rules
        >>> http_alt_rule.insert()
        >>> http_rule.insert()
        >>> # Remove the rules when finished
        >>> http_alt_rule.remove()
        >>> http_rule.remove()
    """
    # pylint: disable=too-many-arguments
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
        self.port = (
            port if proto is not None and proto.lower() in ('tcp', 'udp')
            else None
        )
        self.ipv4 = ipv4
        self.ipv6 = ipv6
        self.qnum = qnum

    def _build_nfqueue_opt(self, h, chain):
        """Returns the options to use for building the NFQUEUE rule.

        Args:
            h: The current hostname to filter on.
            chain: The current chain (changes the direction "src/dst" for
                some options and the queue number).

        Returns:
            A list of parameters that can be used as options in an
            ip(6)tables command.
        """
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
        opt.append('-j')                         # -j
        opt.append('NFQUEUE')                    # NFQUEUE
        opt.append('--queue-num')                # --queue-num
        opt.append(str(self.qnum + chain.qnum))  # <qnum> or <qnum>+1
        return opt

    def _build_rst_opt(self, h, chain):   # pylint: disable=no-self-use
        """Returns the options to use for building the "reset TCP's RST flag"
        rule.

        Args:
            h: The current hostname to filter on.
            chain: The current chain (changes the direction "src/dst" for
                the port).

        Returns:
            A list of parameters that can be used as options in an
            ip(6)tables command.
        """
        opt = []    # A list of iptabales options
        opt.append("OUTPUT")       # OUTPUT
        if h is not None:
            opt.append('-d')            # -d
            opt.append(h)               # <hostname>
        opt.append('-p')                # -p
        opt.append(self.proto)          # <proto>
        if self.port is not None:
            opt.append(chain.port_opt)  # --dport or --sport
            opt.append(str(self.port))  # <port>
        opt.append("--tcp-flags")       # --tcp-flags
        opt.append("RST")               # RST
        opt.append("RST")               # RST
        opt.append("-j")                # -j
        opt.append("DROP")              # DROP
        return opt

    def _insert_or_remove(self, insert=True):
        """Build and then insert or remove the netfilter rules.

        Both operations are regrouped as they are very similary built. The
        only difference is a '-I' or a '-D' in the options.

        Args:
            insert: Inserts the rule if 'True', removes it if 'False'.

        Raises:
            CalledProcessError: An error occurred while running the
                sub-command ip(6)tables.
        """
        # Pre-catch non root errors here instead of letting iptables fail.
        # Because it returns an exitcode of 2 which can indicate something
        # else.
        if os.geteuid() != 0:
            raise PermissionError("You should be root")

        # The binaries to use (IPv4 and/or IPv6) with the associated hostname
        bin_host = []
        if self.ipv4:
            bin_host.append(("/sbin/iptables", self.host))
        if self.ipv6:
            bin_host.append(("/sbin/ip6tables", self.host6))

        # The chains to use (OUTUT and/or INPUT)
        chains = []
        if self.output_chain:
            chains.append(OUTPUT)
        if self.input_chain:
            chains.append(INPUT)

        # The options builders (_build_nfqueue_opt and/or _build_rst_opt)
        opt_builders = [self._build_nfqueue_opt]
        if self.proto is not None and self.proto.lower() == 'tcp':
            opt_builders.append(self._build_rst_opt)

        for binary, h in bin_host:
            for chain in chains:
                for opt_builder in opt_builders:
                    # Build the iptables/ip6tables resulting command
                    cmd = []
                    cmd.append(binary)
                    if insert:
                        cmd.append('-I')
                    else:
                        cmd.append('-D')
                    cmd.extend(opt_builder(h, chain))
                    # Run the command and raise an exception if an error occurs
                    subprocess.run(cmd, check=True)

    def insert(self):
        """Builds and insert the resulting rules in iptables and ip6tables.

        Raises:
            CalledProcessError: exception is raised if an error occurs in the
                process.
        """
        self._insert_or_remove(insert=True)

    def remove(self):
        """Removes the previously inserted rules in iptables and ip6tables.

        Raises:
            CalledProcessError: exception is raised if an error occurs in the
                process.
        """
        self._insert_or_remove(insert=False)


class NFQueue(object):
    """
    Queue object that contains the different packets in the NFQUEUE target.
    It can be iterated over in a for-loop to access them one by one or call
    the `next_packet()` method to access only one packet. The packets are
    either `fragscapy.netfilter.IP` objects or `fragscapy.netfilter.IPv6`
    objects, depending on the `ethertype` parameters received from Layer-2.

    Here is an example of how to setup a proxy from port 8080 to port 80
    (see `fragscapy.netfilter.IP` documentation for how to use the packets):

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
        self._conn.bind(qnum).set_mode(
            fnfqueue.MAX_PAYLOAD, fnfqueue.COPY_PACKET
        )
        self._conn.bind(qnum+1).set_mode(
            fnfqueue.MAX_PAYLOAD, fnfqueue.COPY_PACKET
        )

        # Has the nfqueue been stopped ?
        self._stopped = False

    def __iter__(self):
        return self

    def __next__(self):
        return self.next_packet()

    def next_packet(self):
        """Returns the next packet in NFQUEUE."""
        if self.is_stopped():
            raise StopIteration
        for p in self._conn:
            if p.hw_protocol == scapy.data.ETH_P_IP:
                return IP(p)
            if p.hw_protocol == scapy.data.ETH_P_IPV6:
                return IPv6(p)
            p.accept()
        raise StopIteration

    def is_stopped(self):
        """Has the nfqueue been stopped (i.e. cannot be used anymore) ?"""
        return self._stopped

    def stop(self):
        """Stops the process of the nfqueue by closing the connection."""
        self._stopped = True
        self._conn.close()

    def unbind(self):
        """Unbind all the NFQUEUES."""
        for queue in list(self._conn.queue.values()):
            queue.unbind()


class PacketWrapper(abc.ABC):
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
        self.scapy_pkt = self.l3_layer(pkt.payload)
        self.fnfqueue_pkt = pkt
        self._output = pkt.packet.queue_id % 2 == 0

    @property
    @abc.abstractmethod
    def l3_layer(self):
        """The `scapy` l3-layer constructor to use
        (e.g. `scapy.layers.inet.IP` or `scapy.layers.inet6.IPv6`)."""
        raise NotImplementedError

    @property
    def is_input(self):
        """True if the packet comes from INPUT chain."""
        return not self._output

    @property
    def is_output(self):
        """True if the packet comes from OUTPUT chain."""
        return self._output

    def _apply_modifications(self):
        """Reports the modifications in the Scapy packet to the fnfqueue
        packet."""
        self.fnfqueue_pkt.payload = bytes(self.scapy_pkt)

    def __dir__(self):
        ret = ['scapy_pkt', 'fnfqueue_pkt', 'l3_layer', 'is_input',
               'is_output']
        ret.extend(dir(self.scapy_pkt))
        ret.extend(dir(self.fnfqueue_pkt))
        return ret

    def __getattr__(self, name):
        try:
            return getattr(self.scapy_pkt, name)
        except AttributeError:
            pass
        ret = getattr(self.fnfqueue_pkt, name)
        # When accessing the underlying fnfqueue methods,
        # force to apply the modifications (useful before calling methods
        # such as accept, mangle, verdict, ...)
        self._apply_modifications()
        return ret

    def raw_send(self):
        """Sends the scapy packet directly on a raw socket.

        The charge of dropping the nfqueue packet is left to the user
        (if necessary).
        """
        scapy.sendrecv.send(self.scapy_pkt)



class IP(PacketWrapper):
    """See PacketWrapper documentation."""
    l3_layer = scapy.layers.inet.IP
    __doc__ = PacketWrapper.__doc__


class IPv6(PacketWrapper):
    """See PacketWrapper documentation."""
    l3_layer = scapy.layers.inet6.IPv6
    __doc__ = PacketWrapper.__doc__
