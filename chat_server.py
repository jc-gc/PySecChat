import os
import socket
import time
import tkinter as tk
from datetime import datetime
from queue import Queue
from threading import Thread

import pygubu
from Cryptodome.Cipher import PKCS1_OAEP
from Cryptodome.PublicKey import RSA

import PySecChat

PROJECT_PATH = os.path.dirname(__file__)
PROJECT_UI = PROJECT_PATH + "/server.ui"

NAME = 'Server'
ENCODING = 'utf-8'
BUFFERSIZE = 64
KEYSIZE = 1024

# 0.0.0.0 will bind the server to all network interfaces
addr = ('0.0.0.0', 1252)


class PySecChatServer(PySecChat.PySecChat):
    def __init__(self):
        self.builder = builder = pygubu.Builder()
        builder.add_resource_path(PROJECT_PATH)
        builder.add_from_file(PROJECT_UI)
        self.mainwindow = builder.get_object('frame_1')
        builder.connect_callbacks(self)

        self.clilist = builder.get_object('lstboxClients')
        self.cliscroll = builder.get_object('scrollClients')
        self.clilist.configure(yscrollcommand=self.cliscroll.set)
        self.cliscroll.configure(command=self.clilist.yview)

        self.loglist = builder.get_object('lstboxLog')
        self.logscroll = builder.get_object('scrollLog')
        self.loglist.configure(yscrollcommand=self.logscroll.set)
        self.logscroll.configure(command=self.loglist.yview)

    class message:
        def __init__(self, msg, msgtype, targets):
            self.msg = msg
            self.targets = targets
            self.msgtype = msgtype

            if self.msgtype == 'PK':
                self.data = PySecChatServer.setupPubKey(PySecChatServer, msg)
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

    def updateCliList(self):
        self.clilist.delete(0, tk.END)
        for client in self.clients:
            self.clilist.insert(tk.END, f'{client.address} Enc-{client.rsaestablished}')

    def acceptConnections(self):
        while True:
            try:
                clicon, cliaddr = self.sock.accept()
            except:
                break
            newclient = self.Client(clicon, cliaddr[0])
            self.clients.append(newclient)
            clientThread = Thread(target=self.handleclient, args=(newclient,))
            self.threads.append(clientThread)
            clientThread.start()

    def handleSendQueue(self):
        self.sendqueue = Queue()
        while True:
            msg = self.sendqueue.get()
            if msg != None:
                if msg.targets is not None:
                    for target in msg.targets:
                        if msg.msgtype == 'PK':
                            target.connection.sendall(msg.data)
                        elif msg.msgtype == 'MSG':
                            msg.data = self.setupMsg(target.pubkey.encrypt(msg.msg.encode('utf-8')))
                            target.connection.sendall(msg.data)

    def handleclient(self, client):
        self.loglist.insert(tk.END, f'Client connected from {client.address}')
        self.updateCliList()

        self.loglist.insert(tk.END, f'Sending server pubkey to {client.address}')
        self.sendqueue.put(self.message(self.pubkeybytes, 'PK', [client]))

        full_msg = b''
        new_msg = True

        while 1:
            try:
                data = client.connection.recv(BUFFERSIZE)
            except:
                app.loglist.insert(tk.END, f'Client {client.address} disconnected.')
                self.clients.remove(client)
                self.sendqueue.put(self.message(f'Client {client.address} disconnected.', 'MSG', self.clients))
                self.updateCliList()
                break
            if data:
                if new_msg:
                    try:
                        msgtype = data[:3]
                        msglen = int(data[4:PySecChat.HEADERLEN])
                        new_msg = False
                    except:
                        app.loglist.insert(tk.END, f'Invalid protocol from {client.address}, Disconnecting')
                        client.disconnect()
                        self.clients.remove(client)
                        self.updateCliList()
                        break

                full_msg += data

                if len(full_msg) - PySecChat.HEADERLEN == msglen:
                    if msgtype.decode('utf-8').strip(' ') == 'PK':
                        app.loglist.insert(tk.END, f'PubKey Recieved from {client.address}')
                        srvpubkey = RSA.importKey(full_msg[PySecChat.HEADERLEN:])
                        encryptor = PKCS1_OAEP.new(srvpubkey)
                        client.pubkey = encryptor
                        app.loglist.insert(tk.END, 'Sending ENCTEST message to client')
                        self.sendqueue.put(self.message('ENCTEST', 'MSG', [client]))
                        time.sleep(0.5)
                        self.sendqueue.put(self.message(f'Welcome to the server', 'MSG', [client]))
                        self.sendqueue.put(self.message(f'The time is: {datetime.now()}', 'MSG', [client]))

                    elif msgtype.decode('utf-8').strip(' ') == 'MSG':
                        decrypted = self.srvdecryptor.decrypt(full_msg[PySecChat.HEADERLEN:]).decode('utf-8')

                        if client.rsaestablished is False:
                            if decrypted == 'ENCTEST':
                                client.rsaestablished = True
                                app.loglist.insert(tk.END, f'{client.address} ENCTEST recieved')
                                allbutself = self.clients.copy()
                                allbutself.remove(client)
                                self.sendqueue.put(
                                    self.message(f'Client connected from {client.address}.', 'MSG', allbutself))
                                self.updateCliList()
                            else:
                                app.loglist.insert(tk.END,
                                                   f'Client {client.address} encryption test failed, Disconnecting')
                                client.disconnect()
                        else:
                            app.loglist.insert(tk.END, f'{client.address}: {decrypted}')
                            allbutself = self.clients.copy()
                            allbutself.remove(client)
                            self.sendqueue.put(self.message(f'{client.address}: {decrypted}', 'MSG', allbutself))

                    # playsound.playsound('bing.wav')
                    new_msg = True
                    full_msg = b''

    def getInput(self):
        while True:
            msg = input()
            if msg == 'exit':
                for client in self.clients:
                    client.disconnect()
                self.sock.close()
                exit()

    def exitApp(self):
        for client in self.clients:
            if client is not None:
                client.connection.close()
        self.sock.close()
        exit()

    def run(self):
        self.rsakey = self.createKeys(KEYSIZE)
        self.rsapubkey = self.rsakey.publickey()
        self.pubkeybytes = self.rsapubkey.exportKey(format='PEM')
        self.srvdecryptor = PKCS1_OAEP.new(self.rsakey)

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.bind(addr)
        self.sock.listen(64)

        # Array of clients connected to the server (clientsocket, clientaddress)
        self.clients = []
        # List of active threads
        self.threads = list()

        self.acceptConnThread = Thread(target=self.acceptConnections)
        self.acceptConnThread.setDaemon(True)
        self.threads.append(self.acceptConnThread)
        self.acceptConnThread.start()

        self.getInputThread = Thread(target=self.getInput)
        self.getInputThread.setDaemon(True)
        self.threads.append(self.getInputThread)
        self.getInputThread.start()

        self.sendthread = Thread(target=self.handleSendQueue)
        self.sendthread.setDaemon(True)
        self.threads.append(self.sendthread)
        self.sendthread.start()

        self.mainwindow.mainloop()


if __name__ == '__main__':
    root = tk.Tk()
    app = PySecChatServer()
    app.run()
