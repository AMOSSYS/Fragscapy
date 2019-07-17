## Fragscapy -- Commonly used configuration files

This directory contains examples of configurations files that can be used to
test specific behavior that one may want to test. These files try to test some
corner cases.

### List of configuration files

| Name | Description | Number of tests |
| ---- | ----------- | --------------- |
| ipv4_fragmentation.json | Fragments the IPv4 packets emitted and potentially drop or duplicate some of them and reorder the packets | 72 000 |
| ipv4_overlapping.json | Tries to create overlapping IPv4 fragments that could be used to evade a firewall |60 000 |
| ipv4_tiny_fragments.json | Test only the IPv4 tiny fragments attack i.e. very small fragments | 100 |
| ipv6_fragmentation.json | Fragments the IPv6 packets emitted and potentially drop or duplicate some of them and reorder the packets | 72 000 |
| ipv6_atomic_fragments.json | A single test that creates IPv6 atomic fragments : fragmentation with only 1 fragment. It should not be valid in correct implementations | 1 |
| ipv6_overlapping.json | Tries to create overlapping IPv6 fragments that could be used to evade a firewall |60 000 |
| ipv6_tiny_fragments.json | Test only the IPv6 tiny fragments attack i.e. very small fragments | 100 |
| tcp_segmentation.json | Segment the TCP packets emitted and pottentially drop or duplicate some of them and reorder the segments | 72 000 |
| tcp_overlapping.json | Tries to create overlapping TCP segments that could be used to evade a firewall | 288 000 |
