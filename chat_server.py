import os
import socket
import time
import tkinter as tk
from datetime import datetime
from queue import Queue
from threading import Thread

import pygubu
from Cryptodome import Random
from Cryptodome.Cipher import PKCS1_OAEP
from Cryptodome.PublicKey import RSA

PROJECT_PATH = os.path.dirname(__file__)
PROJECT_UI = PROJECT_PATH + "/server.ui"

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
                        app.builder.get_object('lstboxLog').insert(tk.END, f'{client.address}: {decrypted}')
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
        try:
            clicon, cliaddr = sock.accept()
        except:
            break
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
    app.builder.get_object('lstboxClients').delete(0, tk.END)
    for client in clients:
        app.builder.get_object('lstboxClients').insert(tk.END, f'{client.address} Enc-{client.rsaestablished}')


class ChatServer:
    def __init__(self, root):
        self.builder = builder = pygubu.Builder()
        builder.add_resource_path(PROJECT_PATH)
        builder.add_from_file(PROJECT_UI)
        self.mainwindow = builder.get_object('frame_1')
        builder.connect_callbacks(self)

        clilist = builder.get_object('lstboxClients')
        cliscroll = builder.get_object('scrollClients')
        clilist.configure(yscrollcommand=cliscroll.set)
        cliscroll.configure(command=clilist.yview)

        loglist = builder.get_object('lstboxLog')
        logscroll = builder.get_object('scrollLog')
        loglist.configure(yscrollcommand=logscroll.set)
        logscroll.configure(command=loglist.yview)

    def exitApp(self):
        for client in clients:
            if client is not None:
                client.connection.close()
        sock.close()
        exit()

    def run(self):
        global pubkeybytes, srvdecryptor, threads, sock
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
        self.mainwindow.mainloop()


if __name__ == '__main__':
    root = tk.Tk()
    app = ChatServer(root)
    app.run()
