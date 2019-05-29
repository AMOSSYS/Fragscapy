"""Tool to intercept and modify packets from the network.

Fragscapy is tool that can be used to intercept packets from the network
and modify them using the `Scapy` package. It can be used to automate a lot
of tests and run multiple configurations at once.

The most basic usage is to apply the same modification (e.g. duplicating a
packet, dropping a packet, using fragmentation, ...) to all packets. But it
can also be used to generate a series of tests with slightly differents
parameters each.

This is the intended usage. And to use it, one can either import the different
modules in a python script, use the `commandline` module to use Fragscapy
from a terminal or even use the `fragscapy` command created during the
installation.

On a more advanced usage, Fragscapy can also simply intercept packets and
send them to the user as python objects that can be modified. It can also
be used to apply a series of modifications to pre-generated Scapy packets,
it may be useful when one needs to modify a lot of packets.

Fragscapy can even be extended with many different kind of modifications.
Some basic modifications are already provided but one can add a new one that
better matches his intentions. Though be aware that even if the list of
modifications availables is not limited to the one already existing but it
might require some deep knowledge of the code to create a new one.
"""

from fragscapy._author import __author__
from fragscapy._version import __version__

from fragscapy.commandline import command as main
