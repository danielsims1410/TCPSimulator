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
        print ("[!] Error Transitioning [!]!")
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

# No Connection / Connection Ended
class Closed(State, Transition):
    def __init__(self, Context):
        State.__init__(self, Context)

    # First act of the server - passive open
    def passive_open(self):
        print ("TRANSITION -> Listen")
        self.CurrentContext.setState("LISTEN")
        return True

    # Ends the connection when system says so
    def trigger(self):
        try:
            self.CurrentContext.connection.close()
            self.address = 0
            print ("[!] Closing Connection [!]")
            return True
        except:
            return False

# Listening for Client connection
class Listen(State, Transition):
    def __init__(self, Context):
        State.__init__(self, Context)

    def trigger(self):
        # listen for connections, then transition to Syn Rcvd state
        print ("Waiting for Connection...")
        self.CurrentContext.listen()
        print ("[!] Client Found [!]")
        print ("TRANSITION -> SYN RCVD")
        self.CurrentContext.setState("SYNRCVD")
        return True

# SYN receieved from client
class SynRcvd(State, Transition):
    def __init__(self, Context):
        State.__init__(self, Context)

    def trigger(self):
        # Receive SYN and send SYN+ACK to client,
        # Then waits for client to acknowledge
        # if SYN is not received, then -> Closed

        print ("Waiting on Client...")
        response = self.CurrentContext.connection.recv(1024)
        if response.decode() == "SYN":
            print ("SYN Receieved!")
            print ("Sending SYN + ACK to " + str(self.CurrentContext.connection_address) + "...")
            self.CurrentContext.connection.send("SYN+ACK".encode())
            response = self.CurrentContext.connection.recv(1024)
            if response.decode() == "ACK":
                print ("ACK Received!")
                print ("TRANSITION -> Established")
                self.CurrentContext.setState("ESTABLISHED")
            else:
                print ("[!] Error -> Closed [!]")
                return self.CurrentContext.closed()
        else:
            print ("[!] Error -> Closed [!]")
            return self.CurrentContext.closed()
        return True


class Established(State, Transition):
    def __init__(self, Context):
        State.__init__(self, Context)

    def trigger(self):
    # Receive messages from client
    # If FIN sent over -> Closed
    # Otherwise, received message is displayed & decrypted using same shift value as client
        print ("[!] Receiving Messages [!]\n")
        while True:
            response = self.CurrentContext.connection.recv(1024)
            if response.decode() == "FIN":
                print ("FIN Received!")
                print ("Sending ACK to " + str(self.CurrentContext.connection_address) + "...")
                self.CurrentContext.connection.send("ACK".encode())
                print ("TRANSITION -> Close Wait")
                self.CurrentContext.setState("CLOSEWAIT")
                return True
            else:
                print ("Received: " + response.decode())
                plaintext = caesar_cipher_decrypt(response.decode(), 64)
                print ("Decrypted: " + plaintext + "\n")

class CloseWait(State, Transition):
    def __init__(self, Context):
        State.__init__(self, Context)

    def trigger(self):
        # Sends FIN, trans -> Last ACK to await last acknowledgement
        print ("Sending FIN...")
        self.CurrentContext.connection.send("FIN".encode())
        print ("TRANSITION -> Last ACK!")
        self.CurrentContext.setState("LASTACK")
        return True

class LastAck(State, Transition):
    def __init__(self, Context):
        State.__init__(self, Context)

    def trigger(self):
        # Waiting for final acknowledgement
        print ("Waiting for Client to Acknowledge...")
        response = self.CurrentContext.connection.recv(1024)
        if response.decode() == "ACK":
            print ("Last ACK received!")
            print ("TRANSITION -> Closed")
            self.CurrentContext.setState("CLOSED")
        return True


class TCPSimulatorServer(StateContext, Transition):
    def __init__(self):
        #loopback address
        self.host = "127.0.0.1"
        self.port = 5000
        self.connection_address = 0
        self.socket = None
        self.availableStates["CLOSED"] = Closed(self)
        self.availableStates["LISTEN"] = Listen(self)
        self.availableStates["SYNRCVD"] = SynRcvd(self)
        self.availableStates["ESTABLISHED"] = Established(self)
        self.availableStates["CLOSEWAIT"] = CloseWait(self)
        self.availableStates["LASTACK"] = LastAck(self)
        print ("INITIAL STATE -> Closed")
        self.setState("CLOSED")

    def listen(self):
        # Uses socket to find connection
        self.socket = socket()
        try:
            self.socket.bind((self.host, self.port))
            self.socket.listen(1)
            self.connection, self.connection_address = self.socket.accept()
            return True
        except Exception as e:
            print (e)
            exit()

    def closed(self):
        return self.CurrentState.passive_open()

    def synrcvd(self):
        return self.CurrentState.synrcvd()

    def established(self):
        return self.CurrentState.established()

    def closedwait(self):
        return self.CurrentState.closedwait()

    def lastack(self):
        return self.CurrentState.lastack()

# Decrypt incoming messagess
def caesar_cipher_decrypt(input, shift):
    result = ""
    for i in range(len(input)):
        char = input[i]
        if(char.isupper()): #to keep uppercase
            result += chr((ord(char) - shift - 65) % 26 + 65)
        else:
            result += chr((ord(char) - shift - 97) % 26 + 97)
    return result



if __name__ == "__main__":
    print ("== TCP Simulator Server ==================")
    simulator = TCPSimulatorServer()
    simulator.closed()
    print ("===========================================")
