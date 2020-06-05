import socket
import time
import tkinter as tk
from datetime import datetime
from queue import Queue
from threading import Thread

from Cryptodome import Random
from Cryptodome.Cipher import PKCS1_OAEP
from Cryptodome.PublicKey import RSA

sendqueue = Queue()

HEADERLEN = 8
NAME = 'Server'
ENCODING = 'utf-8'
BUFFERSIZE = 64
KEYSIZE = 1024

# 0.0.0.0 will bind the server to all network interfaces
addr = ('0.0.0.0', 1252)

# Array of clients connected to the server (clientsocket, clientaddress)
clients = []
# List of active threads
threads = list()


def createKeys(size):
    print('Generating RSA Keys')
    random_generator = Random.new().read
    key = RSA.generate(size, random_generator)
    print('Done')
    return key


class message:
    def __init__(self, msg, msgtype, targets):
        self.msg = msg
        self.targets = targets
        self.msgtype = msgtype

        if self.msgtype == 'PK':
            self.data = setupPubKey(msg)
        else:
            self.data = None


class Client:
    def __init__(self, socket, address):
        self.connection = socket
        self.address = address
        self.pubkey = None  # Used to encrypt messages to send to the client
        self.rsaestablished = False

    def disconnect(self):
        self.connection.close()

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
    data = f'{"MSG":<{4}}{len(msg):<{4}}'.encode('utf-8') + msg
    return data


def setupPubKey(key):
    data = f'{"PK":<{4}}{len(key):<{4}}'.encode('utf-8') + key
    return data


def handleclient(client):
    print('Client connected from ' + client.address)
    updateCliList()

    print('Sending server pubkey to client')
    sendqueue.put(message(pubkeybytes, 'PK', [client]))

    # Announce new connection to all other clients
    allbutself = clients.copy()
    allbutself.remove(client)
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
                    print('Sending ENCTEST message to client')
                    sendqueue.put(message('ENCTEST', 'MSG', [client]))
                    time.sleep(0.5)
                    sendqueue.put(message(f'Welcome to the server', 'MSG', [client]))
                    sendqueue.put(message(f'The time is: {datetime.now()}', 'MSG', [client]))

                elif msgtype.decode('utf-8').strip(' ') == 'MSG':
                    decrypted = srvdecryptor.decrypt(full_msg[HEADERLEN:]).decode('utf-8')

                    if client.rsaestablished is False:
                        if decrypted == 'ENCTEST':
                            client.rsaestablished = True
                            print(f'{client.address} ENCTEST recieved')
                            updateCliList()
                        else:
                            print(f'Client {client.address} encryption test failed, Disconnecting')
                            client.disconnect()
                    else:
                        print(f'<{client.address}>: {decrypted}')
                        allbutself = clients.copy()
                        allbutself.remove(client)
                        sendqueue.put(message(f'{client.address}: {decrypted}', 'MSG', allbutself))

                # playsound.playsound('bing.wav')
                new_msg = True
                full_msg = b''


def handleSendQueue():
    while 1:
        msg = sendqueue.get()
        if msg != None:
            if msg.targets is not None:
                for target in msg.targets:
                    if msg.msgtype == 'PK':
                        target.connection.sendall(msg.data)
                    elif msg.msgtype == 'MSG':
                        msg.data = setupMsg(target.pubkey.encrypt(msg.msg.encode('utf-8')))
                        target.connection.sendall(msg.data)


def acceptConnections():
    while 1:
        clicon, cliaddr = sock.accept()
        newclient = Client(clicon, cliaddr[0])
        clients.append(newclient)
        x = Thread(target=handleclient, args=(newclient,))
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


key = createKeys(KEYSIZE)
pubkey = key.publickey()
pubkeybytes = pubkey.exportKey(format='PEM')
srvdecryptor = PKCS1_OAEP.new(key)

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.bind(addr)
sock.listen(64)

x = Thread(target=acceptConnections)
x.setDaemon(True)
threads.append(x)
x.start()

y = Thread(target=getInput)
y.setDaemon(True)
threads.append(y)
y.start()

sendthread = Thread(target=handleSendQueue)
sendthread.setDaemon(True)
threads.append(sendthread)
sendthread.start()

tk.mainloop()
