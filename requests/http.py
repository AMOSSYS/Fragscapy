from scapy.all import IPv6, TCP, send, sr1, sniff
from random import randint

class HTTP:
    def __init__(self, hostname, dport=80):
        self.hostname = hostname
        self.http_host = ""
        self.dport = 80
        self.sport = randint(1025, 0xffff)

        self.state = 0
        self.seq = 0
        self.ack = 0

    def three_way_handshake(self):
        if self.state == 0:
           syn = IPv6(dst=self.hostname)/TCP(sport=self.sport, dport=self.dport, flags="S")
           synack = sr1(syn)
           self.state = 1
           self.seq = synack['TCP'].ack
           self.ack = synack['TCP'].seq + 1

    def get(self, path):
        if (self.state == 0):
            self.three_way_handshake()
        http_req = "GET {path} HTTP/1.1\r\nHost: {http_host}\r\n\r\n".format(path=path, http_host=self.http_host)
        http_filter = "ip6 and src {ip} and src port {sport} and dst port {dport}".format(
                ip=self.hostname, sport=self.dport, dport=self.sport)
        get = IPv6(dst=self.hostname)/TCP(sport=self.sport, dport=self.dport, seq=self.seq, ack=self.ack, flags='A')/http_req
        reply = sr1(get)
        other_reply = sniff(filter=http_filter, timeout=10, count=1)
        if len(other_reply) == 1:
            if other_reply[0].haslayer('Raw'):
                print(other_reply[0]['Raw'].load.decode())
            else:
                print("Missing Raw layer. See full packet")
                other_reply[0].display()
        else:
            print("No response from server")


if __name__ == '__main__':
    ip_dst = input("IPv6 dest [fd02::1]: ") or "fd02::1"
    path = input("URL Path [/]: ") or "/"
    HTTP(ip_dst).get(path)
