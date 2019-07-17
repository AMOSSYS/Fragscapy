## Fragscapy -- Commonly used configuration files

This directory contains examples of configurations files that can be used to
test specific behavior that one may want to test. These files try to test some
corner cases.

### List of configuration files

| Name | Description |
| ---- | ----------- |
| ipv4_fragmentation.json | Fragments the IPv4 packets emitted and potentially drop or duplicate some of them and reorder the packets |
| ipv4_overlapping.json | Tries to create overlapping IPv4 fragments that could be evade a firewall |
| ipv4_tiny_fragments.json | Test only the IPv4 tiny fragments attack i.e. very small fragments |
| ipv6_fragmentation.json | Fragments the IPv6 packets emitted and potentially drop or duplicate some of them and reorder the packets |
| ipv6_atomic_fragments.json | A single test that creates IPv6 atomic fragments : fragmentation with only 1 fragment. It should not be valid in correct implementations |
| ipv6_overlapping.json | Tries to create overlapping IPv6 fragments that could be evade a firewall |
| ipv6_tiny_fragments.json | Test only the IPv6 tiny fragments attack i.e. very small fragments |
| ipv4_or_ipv6_fragmentation.json | Fragments the IPv4 and Ipv6 packets emitted and potentially drop or duplicate some of them and reorder the packets |
| ipv4_or_ipv6_overlapping.json | Tries to create overlapping IPv4 and IPv6 fragments that could be evade a firewall |
| ipv4_or_ipv6_tiny_fragments.json | Test only the IPv4 and IPv6 tiny fragments attack i.e. very small fragments |
