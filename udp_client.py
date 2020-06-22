import socket
import threading
import json
from utils import *


class Client:
    peer_addr = None
    ping_addr = None
    perform_ping = False
    perform_punch = False

    def __init__(self, username, server_addr, peername=None):
        self.state = InitialState(self)
        self.username = username
        self.server_addr = server_addr
        self.peername = peername
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        if self.peername:
            self.sock.sendto(
                self._create_message(
                    signal = Signal.REGISTER_AND_CONNECT,
                    user = self.username,
                    peer = self.peername,
                ),
                self.server_addr
            )          
        else:
            self.sock.sendto(
                self._create_message(
                    signal = Signal.REGISTER_AND_WAIT,
                    user = self.username
                ),
                self.server_addr
            )

        while type(self.state) != PeerConnectedState:
            message = self.__get_response()
            self.state.handle(message)

        print(f'Connection Established Between users {self.username}:{self.peername}')
        # Now use self.sock to exchange messages

    def _create_message(self, signal, **kwargs):
        return json.dumps(dict( signal=signal, **kwargs)).encode('utf-8')

    def __get_response(self, buff_size=1024):
        response = self.sock.recv(buff_size)
        return json.loads(response.decode('utf-8'))

    def __ping(self):
        self.sock.sendto(
            self._create_message(signal=Signal.PING),
            self.ping_addr
        )
        if self.perform_ping:
            threading.Timer(self.ping_interval, self.__ping).start()

    def __punch(self):
        self.sock.sendto(
            self._create_message(signal=Signal.PUNCH),
            self.peer_addr
        )
        if self.perform_punch:
            threading.Timer(interval=0.5, function=self.__punch).start()
    
    def change_state(self, state: State):
        # print(f'Changing state {type(self.state).__name__} -> {state.__name__}') # DEBUG
        self.state = state(client=self)

    def get_state(self):
        return self.state

    def set_peer(self, peername, peer_addr: tuple):
        self.peername = peername
        self.peer_addr = tuple(peer_addr)

    def set_ping_addr(self, addr: tuple, interval: int=5):
        self.ping_addr = addr
        self.ping_interval = interval
    
    def enable_ping_activity(self, perform: bool):
        self.perform_ping = perform
        if self.perform_ping:
            self.__ping()

    def enable_punch_activity(self, perform: bool):
        self.perform_punch = perform
        if self.perform_punch:
            self.__punch()
    
    def send_msg(self, signal=Signal.CHAT, msg=''): # Send msg to peer
        self.sock.sendto(
            self._create_message(signal=signal, msg=msg),
            self.peer_addr
        )
