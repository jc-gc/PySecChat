import queue
import socket
import threading
import tkinter as tk

from Cryptodome import Random
from Cryptodome.Cipher import PKCS1_OAEP
from Cryptodome.PublicKey import RSA


def createKeys():
    random_generator = Random.new().read
    key = RSA.generate(1024, random_generator)
    return key


class message:
    def __init__(self, msg, type, targets):
        self.msg = msg
        self.targets = targets
        self.type = type

        if self.type == 'PK':
            self.data = setupPubKey(msg)
        elif self.type == 'MSG':
            self.data = setupMsg(msg)
        else:
            self.data = None

class Client:
    def __init__(self, socket, address):
        self.connection = socket
        self.address = address
        self.pubkey = None
        self.rsaestablished = False

    def disconnect(self):
        self.connection.close()


sendqueue = queue.Queue()

HEADERLEN = 8
NAME = 'Server'
ENCODING = 'utf-8'
BUFFERSIZE = 64

# 0.0.0.0 will bind the server to all network interfaces
addr = ('0.0.0.0', 1252)

# Array of clients connected to the server (clientsocket, clientaddress)
clients = []
# List of active threads
threads = list()

######

cliListWin = tk.Tk()
cliListWin.title("Clients")

cliListFrame = tk.Frame(cliListWin)
clistr = tk.StringVar()  # For the messages to be sent.
clistr.set("")
scrollbar = tk.Scrollbar(cliListFrame)  # To navigate through past messages.
# Following will contain the messages.
cliListbox = tk.Listbox(cliListFrame, height=15, width=35, yscrollcommand=scrollbar.set)
cliListbox.configure(bg="#333333", fg='#ffffff')
scrollbar.configure(command=cliListbox.yview, bg='#000000')
scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
cliListbox.pack(side=tk.LEFT, fill=tk.BOTH)
cliListbox.configure(yscrollcommand=scrollbar.set)

cliListbox.pack()
cliListFrame.pack()


######

def setupMsg(msg):
    data = f'{"MSG":<{4}}{len(msg):<{4}}{msg}'
    return data


def setupPubKey(key):
    data = f'{"PK":<{4}}{len(key):<{4}}'.encode('utf-8') + key
    return data

def handleclient(client):
    print('Client connected from ' + client.address)
    updateCliList()

    allbutself = clients.copy()
    allbutself.remove(client)

    sendqueue.put(message(pubkeybytes, 'PK', [client]))

    # Announce new connection to all other clients
    sendqueue.put(message(f'Client connected from {client.address}.', 'MSG', allbutself))

    full_msg = b''
    new_msg = True

    while 1:
        try:
            data = client.connection.recv(BUFFERSIZE)
        except:
            print(f'Client {client.address} disconnected.')
            clients.remove(client)
            sendqueue.put(message(f'Client {client.address} disconnected.', 'MSG', clients))
            updateCliList()
            break
        if data:
            if new_msg:
                msgtype = data[:3]
                msglen = int(data[4:HEADERLEN])
                new_msg = False

            full_msg += data

            if len(full_msg) - HEADERLEN == msglen:
                if msgtype.decode('utf-8').strip(' ') == 'PK':
                    print(f'PubKey Recieved from {client.address}')
                    srvpubkey = RSA.importKey(full_msg[HEADERLEN:])
                    encryptor = PKCS1_OAEP.new(srvpubkey)
                    client.pubkey = encryptor

                elif msgtype.decode('utf-8').strip(' ') == 'MSG':
                    decrypted = srvdecryptor.decrypt(full_msg[HEADERLEN:]).decode('utf-8')

                    if client.rsaestablished is False:
                        if decrypted == 'ENCTEST':
                            client.rsaestablished = True
                            print(f'{client.address} Encryption Established')
                            updateCliList()
                        else:
                            print(f'Client {client.address} encryption test failed, Disconnecting')
                            client.disconnect()

                # playsound.playsound('bing.wav')
                new_msg = True
                full_msg = b''


def handleSendQueue():
    while 1:
        msg = sendqueue.get()
        if msg != None:
            for target in msg.targets:
                target.connection.sendall(msg.data)


def acceptConnections():
    while 1:
        clicon, cliaddr = sock.accept()
        newclient = Client(clicon, cliaddr[0])
        clients.append(newclient)
        x = threading.Thread(target=handleclient, args=(newclient,))
        threads.append(x)
        x.start()


def getInput():
    while 1:
        msg = input()
        if msg == 'exit':
            for client in clients:
                client.disconnect()
            sock.close()
            exit()


def updateCliList():
    cliListbox.delete(0, tk.END)
    for client in clients:
        cliListbox.insert(tk.END, f'{client.address} Enc-{client.rsaestablished}')


key = createKeys()
pubkey = key.publickey()
pubkeybytes = pubkey.exportKey(format='PEM')
srvdecryptor = PKCS1_OAEP.new(key)

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.bind(addr)
sock.listen(64)

x = threading.Thread(target=acceptConnections)
x.setDaemon(True)
threads.append(x)
x.start()

y = threading.Thread(target=getInput)
y.setDaemon(True)
threads.append(y)
y.start()

sendthread = threading.Thread(target=handleSendQueue)
sendthread.setDaemon(True)
threads.append(sendthread)
sendthread.start()

tk.mainloop()
