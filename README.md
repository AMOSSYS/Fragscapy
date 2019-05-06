# FragScapy

This project aims at reproducing a fragroute like behavior for Scapy packets. The goal is to first support the IPv6 packets manipulation.

## Setup

You then can either install the package to use iti as a standard package:
```
./setup build
./setup install
```
Or install it for development:
```
pip install -r requirements.txt
```

## Usage

_note : It might be useful to prevent your OS from sending RST packets because it is not aware a TCP connection is handled by Scapy in the user space. With iptables it can be done by adding the following rule:
```
iptables -A OUTPUT -p tcp --tcp-flags RST RST -s <local_ip> -j DROP
```
_

To use this package, you need to create two lists:
* A `fragscapy.PacketList` that will contains the Scapy packets to modify and then send
* A `fragscapy.ModList` that will contains a succession of modifications to apply

The `PacketList` is used to store some Scapy packets together and specify an optional delay between each.
```python
from fragscapy import PacketList
from scapy.all import IPv6, TCP

pl = PacketList
pl.add_packet(IPv6()/TCP()/"DATA")
pl.add_packet(IPv6()/TCP(dport=8080)/"OTHER DATA")
pl.add_packet(IPv6()/TCP()/"DELAYED DATA", delay=10)
pl.send()
```

The `ModList` is used to store in a specific order a set of modifications that are to apply on a `PacketList`
```python
from fragscapy import ModList, ModDuplicate, ModEcho

# Short info on the usage of the Modification
print(ModDuplicate.usage())

ml = ModList()
ml.append(ModEcho("START"))
ml.append(ModDuplicate("random"))
ml.append(ModEcho("END"))
pl = ml.apply(pl)
pl.send()
```

The possible modifications available so far are :
* _ModDropOne_ : Drops one packet
* _ModDropProba_ : Drops each packet with a certain probability
* _ModEcho_ : Echoes a string
* _ModPrint_ : Print the content of each packet
* _ModDuplicate_ : Duplicate one of the packet
* _ModReorder_ : Change the order of the packet list
* _ModSelect_ : Keeps only a subset of the packets
* _ModFragment6_ : Add some IPv6 fragmentation to each packet
Of course this list can be extend by implementing `fragscapy.modifications.Mod`. Refers to each Modification documentation for a more detailed explanation on how to use them.

## Exemples

```python
from fragscapy import ModList, ModEcho, ModFragment
from requests.http import HTTP6

ml = ModList()
ml.append(ModEcho("Start"))
ml.append(ModFragment(100))
ml.append(ModEcho("End"))

responses = HTTP6("www.exemple.com", modlist=ml).get()
for response in responses:
    print(response)
