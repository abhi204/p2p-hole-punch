class Signal:
    REGISTER_AND_WAIT = 0 # register and wait for peer to connect to you
    REGISTER_AND_CONNECT = 1 # register and send the peername you want to connect to
    ACK_REGISTER = 2
    PEER_INFO = 3
    PUNCH = 4
    ACK_PUNCH = 5
    PING = 6
    CHAT = 7 # Message signal between peers after Hole-punching is successful


# States of Client instance througout the hole-punching cycle
class State:
    def __init__(self, client):
        self.client = client

    def handle(self, message):
        raise NotImplementedError

    def log_unhandled_signal(self, signal: str):
        print(f"[Warning] Ignoring signal: {signal} recieved in state: {type(self).__name__} ")


class InitialState(State):
    def __init__(self, client):
        super().__init__(client)

    def handle(self, message):
        signal = message.get('signal')
        if signal == Signal.ACK_REGISTER: # client is the initiator of connection
            self.client.change_state(RegisteredState)
        elif signal == Signal.PEER_INFO: # client is not the initiator 
            self.client.set_peer(peername=message.get('peer'), peer_addr=message.get('peer_addr'))
            self.client.change_state(PeerConnectingState)
        else:
            self.log_unhandled_signal(signal)

class RegisteredState(State):

    def __init__(self, client):
        super().__init__(client)
        self.client.set_ping_addr(self.client.server_addr)
        self.client.enable_ping_activity(True) # start server pings

    def handle(self, message):
        signal = message.get('signal')
        if signal == Signal.PEER_INFO:
            self.client.set_peer(peername=message.get('peer'), peer_addr=message.get('peer_addr'))
            self.client.change_state(PeerConnectingState)
        else:
            self.log_unhandled_signal(signal)

class PeerConnectingState(State):

    def __init__(self, client):
        super().__init__(client)
        self.client.enable_ping_activity(False) # stop server pings
        self.client.enable_punch_activity(True) # start UDP hole punching

    def handle(self, message):
        signal = message.get('signal')
        if signal == Signal.ACK_PUNCH: # punch cycle complete
            self.client.change_state(PeerConnectedState)
        elif signal == Signal.PUNCH: # hole punching successful
            self.client.send_msg(signal=Signal.ACK_PUNCH)
            self.client.change_state(PeerConnectedState)
        else:
            self.log_unhandled_signal(signal)

class PeerConnectedState(State):
    '''
    This is the final state the client needs to be in
    '''
    def __init__(self, client):
        super().__init__(client)
        self.client.enable_punch_activity(False) # stop UDP hole punching
        self.client.set_ping_addr(self.client.peer_addr, interval=10)
        self.client.enable_ping_activity(True) # start peer pings

    def handle(self, message):
        '''
        Client handles the messages
        '''
        pass
