## Fragscapy -- Configuration files examples

This directory contains various configuration files that can be used with
FragScapy. They are not intendended to be revelant, they are just here to
show the possibilities. Though most of the configuration files are valid.

For more relevant, i.e. applicable to real testing, configuration files, see
[_config\_common_ directory](config_common/).

### List of configuration files

| Name | Valid | Description |
| ---- | ----- | ----------- |
| 00_template.json | ✖ | Describes all the fields that can appear in a config file |
| 01_ping_no_mod.json | ✔ | Start a simple ping but does not apply any modification to the packets |
| 02_ping_duplicate.json | ✔ | Ping a host but duplicate each packet sent out |
| 03_http_fragment6.json | ✔ | Wget on a server. All IPv6 packets sent out are fragmented with a size that vary from 50 to 10000 with a step of 50 |
| 04_http_proxy.json | ✔ | Creates a TCP-port proxy from 8080 to 80. The packets sent to 8080 are modified to be sent to 80 and packets received from 80 are modified to be received from 8080 |
| 05_complete_mess.json | ✔ | Does not make a lot of sense. It just apply most of the modifications (with non-relevant parameters) onto a wget command. Mosts of the tests should not pass because the resulting packets makes no sense at all |
| 06_tcp_segmentation.json | ✔ | Wget command on a server but tcp packets are segmented with a size that vary from 4 to 200 with a step of 1 |
