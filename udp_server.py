# server.py
import socket
import json
import collections
from utils import Signal


class Server:
    table = collections.defaultdict(list) # stores username: ip_address(s) mapping
    waitlist = collections.defaultdict(set) # stores details of users waiting for the peer to register on this server 

    def create_message(self, signal, **kwargs):
        return json.dumps(dict( signal=signal, **kwargs)).encode('utf-8')

    def __init__(self, port=12345):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(("0.0.0.0", port))
        print("listening on *:%d (udp)" % port)
        self.runserver()


    def runserver(self):
        while True:
            msg, addr = self.sock.recvfrom(1024)
            msg = json.loads(msg.decode('utf-8')) # convert msg to dict
            signal = msg.get('signal')

            if signal == Signal.REGISTER_AND_WAIT: # Register IP to a Name in Table
                user = msg['user']
                self.table[user].append(addr) # Add new client socket addr to table
                if self.waitlist.get(user) and len(self.waitlist.get(user)):
                    peer = self.waitlist.get(user).pop()
                    self.cross_connect(user, peer)
                else:
                    self.sock.sendto(
                        self.create_message(signal=Signal.ACK_REGISTER),
                        addr
                    )
            elif signal == Signal.REGISTER_AND_CONNECT:
                user = msg['user']
                peer = msg['peer']
                self.table[user].append(addr) # Add new client socket addr to table
                if self.table.get('peer'): # peer already registered with Signal.REGISTER_AND_WAIT
                    self.cross_connect(user, peer)
                else: # peer has to Signal.REGISTER_AND_WAIT
                    self.waitlist[peer].add(user)
                    self.sock.sendto(
                        self.create_message(signal=Signal.ACK_REGISTER),
                        addr
                    )
            elif signal == Signal.PING:
                # Ping signal ensures that NAT doesn't change the public ip:port of client socket is available
                pass
            else:
                # Unknown Signal encountered (Maybe log this)
                pass

    
    def cross_connect(self, client_a, client_b):
        addr_a = self.table.get(client_a).pop()
        addr_b = self.table.get(client_b).pop()

        self.sock.sendto(
            self.create_message(
                signal=Signal.PEER_INFO,
                peer=client_a,
                peer_addr=addr_a
            ),
            addr_b
        )

        self.sock.sendto(
            self.create_message(
                signal=Signal.PEER_INFO,
                peer=client_b,
                peer_addr=addr_b
            ),
            addr_a
        )
        print("IP exchange between users: ", addr_a, addr_b)

Server()