import datetime
import queue
import socket
import threading
import time
import tkinter as tk

from Cryptodome import Random
from Cryptodome.PublicKey import RSA


def createKeys():
    random_generator = Random.new().read
    key = RSA.generate(1024, random_generator)
    return key


class message:
    def __init__(self, msg, name, source, targets):
        self.msg = msg
        self.name = name
        self.source = source
        self.targets = targets


class Client:
    def __init__(self, socket, address):
        self.connection = socket
        self.address = address
        self.pubkey = None

    def disconnect(self):
        self.connection.close()


sendqueue = queue.Queue()

HEADERLEN = 16
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

def setupMsg(message, name):
    msg = f'{len(message):<{3}} {name:<{12}}' + message
    msg = msg.encode(ENCODING)
    return msg


def handleclient(client):
    print('Client connected from ' + client.address)
    updateCliList()

    # Announce new connection to all other clients
    sendqueue.put(message(f'Client connected from {client.address}.', NAME, client.connection, clients))

    time.sleep(0.05)
    sendqueue.put(message(f'Welcome to the server.', NAME, None, [client]))
    sendqueue.put(message("The time is: " + str(datetime.datetime.now()), NAME, None, [client]))

    full_msg = ''
    new_msg = True

    while 1:
        try:
            data = client.connection.recv(BUFFERSIZE)
        except:
            print(f'Client {client.address} disconnected.')
            sendqueue.put(message(f'Client {client.address} disconnected.', NAME, client.connection, clients))
            clients.remove(client)
            updateCliList()
            break
        if data:
            if new_msg:
                msglen = int(data[:3])
                sendername = data[4:HEADERLEN].decode('utf-8').strip(' ')
                new_msg = False

            full_msg += data.decode("utf-8")

            if len(full_msg) - HEADERLEN == msglen:
                print(f'<{client.address}> {sendername}: {full_msg[HEADERLEN:]}')

                sendqueue.put(message(full_msg[HEADERLEN:], sendername, client.connection, clients))
                new_msg = True
                full_msg = ''


def handleSendQueue():
    while 1:
        msg = sendqueue.get()
        if msg != None:
            for target in msg.targets:
                if target.connection != msg.source:
                    target.connection.sendall(setupMsg(msg.msg, msg.name))


def acceptConnections():
    while 1:
        clicon, cliaddr = sock.accept()
        newclient = Client(clicon, cliaddr[0])
        print(newclient.address)
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
        cliListbox.insert(tk.END, f'{client.address}')


key = createKeys()
pubkey = key.publickey().exportKey(format='PEM')

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

print('Running')

tk.mainloop()
