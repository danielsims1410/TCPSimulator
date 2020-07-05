from socket import socket

class State:
    CurrentContext = None
    def __init__(self, Context):
        self.CurrentContext = Context
    def trigger(self):
        return True

class StateContext:
    state = None
    CurrentState = None
    availableStates = {}

    def setState(self, newstate):
        try:
            self.CurrentState = self.availableStates[newstate]
            self.state = newstate
            self.CurrentState.trigger()
            return True
        except KeyError: #incorrect state key specified
            return False

    def getStateIndex(self):
        return self.state

class Transition:
    def passive_open(self):
        print ("[!] Error Transitioning [!]")
        return False

    def syn(self):
        print ("[!] Error Transitioning [!]!")
        return False

    def ack(self):
        print ("[!] Error Transitioning [!]!")
        return False

    def rst(self):
        print ("[!] Error Transitioning [!]!")
        return False

    def syn_ack(self):
        print ("[!] Error Transitioning [!]!")
        return False

    def close(self):
        print ("[!] Error Transitioning [!]!")
        return False

    def fin(self):
        print ("[!] Error Transitioning [!]!")
        return False

    def timeout(self):
        print ("[!] Error Transitioning [!]!")
        return False

    def active_open(self):
        print ("[!] Error Transitioning [!]!")
        return False

class Closed(State, Transition):
    def __init__(self, Context):
        State.__init__(self, Context)

    def active_open(self):
        # Initiates three-way handshake
        self.CurrentContext.connection()
        print ("Connecting to " + str(self.CurrentContext.connection_address) + "...")
        print ("Sending SYN to " + str(self.CurrentContext.connection_address) + "...")
        self.CurrentContext.socket.send("SYN".encode())

        print ("TRANSITION -> SYN SENT")
        self.CurrentContext.setState("SYNSENT")
        return True

    def trigger(self):
        #  Final ACK has been sent!
        try:
            self.CurrentContext.socket.close()
            self.address = 0
            print ("[!] Closing Connection [!]")
            return True
        except:
            return False

class SynSent(State, Transition):
    def __init__(self, Context):
        State.__init__(self, Context)

    def trigger(self):
        # Waits for SYN+ACK
        # Then sends ACK command -> Established.
        # if !SYN+ACK -> Closed.
        print ("Waiting on server...")
        response = self.CurrentContext.socket.recv(1024)
        if response.decode() == "SYN+ACK":
            print ("SYN+ACK Received from " + str(self.CurrentContext.connection_address) + "!")
            print ("Sending ACK to " + str(self.CurrentContext.connection_address) + "...")
            self.CurrentContext.socket.send("ACK".encode())
            print ("TRANSITION -> Established")
            self.CurrentContext.setState("ESTABLISHED")
        else:
            print ("[!] Timeout Occured - Transitioning to Closed [!]")
            return self.CurrentContext.closed()
        return True

class Established(Transition, State):
    def __init__(self, Context):
        State.__init__(self, Context)

    def trigger(self):
        # Send messages to the server which are then encrypted using same shift value as server
        # TODO: User chooses this value?
        # User enters close -> FIN sent, Trans to FIN WAIT-1
        print ("[!] Connection Established - 'Close' to Exit [!]\n")
        user_input = input("Enter Message: ")
        while user_input.lower() != "close":
            encrypted_text = caesar_cipher_encrypt(user_input, 64)
            print ("Encrypting...")
            print ("Sending: " + str(encrypted_text) + "\n")
            self.CurrentContext.socket.send(encrypted_text.encode())
            user_input = input("Message: ")
        if user_input.lower() == "close":
            print ("Sending FIN to " + str(self.CurrentContext.connection_address) + "...")
            self.CurrentContext.socket.send("FIN".encode())
            print ("TRANSITION -> FIN WAIT-1")
            self.CurrentContext.setState("FINWAIT1")


class FinWait1(State, Transition):
    def __init__(self, Context):
        State.__init__(self, Context)

    def trigger(self):
        # Waits for ACK from Server
        # -> FIN WAIT-2
        print ("Waiting on server to acknowledge...")
        response = self.CurrentContext.socket.recv(1024)
        if response.decode() == "ACK":
            print ("ACK Received!")
            print ("TRANSITION -> FIN WAIT-2")
            self.CurrentContext.setState("FINWAIT2")
        return True

class FinWait2(State, Transition):
    def __init__(self, Context):
        State.__init__(self, Context)

    def trigger(self):
        # Waits for FIN from Server
        # -> Send ACK to Server -> Trans to TIMED WAIT
        print ("Waiting on server...")
        response = self.CurrentContext.socket.recv(1024)
        if response.decode() == "FIN":
            print ("FIN Received!")
            print ("Sending ACK to " + str(self.CurrentContext.connection_address) + "...")
            self.CurrentContext.socket.send("ACK".encode())
            print ("TRANSITION -> Timed Wait")
            self.CurrentContext.setState("TIMEDWAIT")
        return True

class TimedWait(State, Transition):
    def __init__(self, Context):
        State.__init__(self, Context)

    def trigger(self):
        # -> Straight to Closed state
        print ("TRANSITION -> Closed")
        self.CurrentContext.setState("CLOSED")
        return True

class TCPSimulatorClient(StateContext, Transition):
    def __init__(self):
        self.host = "127.0.0.1"
        self.port = 5000
        self.connection_address = 0
        self.socket = None
        
        # Establishing states
        self.availableStates["CLOSED"] = Closed(self)
        self.availableStates["ESTABLISHED"] = Established(self)
        self.availableStates["SYNSENT"] = SynSent(self)
        self.availableStates["FINWAIT1"] = FinWait1(self)
        self.availableStates["FINWAIT2"] = FinWait2(self)
        self.availableStates["TIMEDWAIT"] = TimedWait(self)

        #ref diagram, first state is closed
        print ("INITIAL STATE -> Closed")
        self.setState("CLOSED")

    def connection(self):
        # Connects to a socket
        self.socket = socket()
        try:
            self.socket.connect((self.host, self.port))
            self.connection_address = self.host
        except Exception as e:
            print (e)
            exit()

    def closed(self):
        return self.CurrentState.active_open()

    def established(self):
        return self.CurrentState.established()

    def synsent(self):
        return self.CurrentState.synsent()

    def finwait1(self):
        return self.CurrentState.finwait1()

    def finwait2(self):
        return self.CurrentState.finwait2()

    def timedwait(self):
        return self.CurrentState.timedwait()

def caesar_cipher_encrypt(input, shift):
    result = ""
    for i in range(len(input)): # for every character in the input...
        char = input[i]
        if(char.isupper()): #to keep uppercase on decryption
            result += chr((ord(char) + shift-65) % 26 + 65) #shift character
        else:
            result += chr((ord(char) + shift - 97) % 26 + 97)
    return result

if __name__ == "__main__":
    print ("== TCP Simulator Client ==================")
    simulator = TCPSimulatorClient()
    simulator.closed()
    print ("==========================================")
