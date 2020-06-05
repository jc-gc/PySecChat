#!/usr/bin/env python
"""Script for Tkinter GUI chat client."""
import atexit
import os
import socket
import tkinter as tk
from random import randint
from threading import Thread

import pygubu
from Cryptodome import Random
from Cryptodome.Cipher import PKCS1_OAEP
from Cryptodome.PublicKey import RSA

PROJECT_PATH = os.path.dirname(__file__)
PROJECT_UI = PROJECT_PATH + "/chatclient.ui"

HEADERLEN = 8
NAME = f'guiCl-{randint(100, 999)}'
ENCODING = 'utf-8'
BUFFERSIZE = 64
# Size of RSA key to generate
KEYSIZE = 1024

# Use 127.0.0.1 to connect to server running on your own pc
SERVER_ADDR = ('127.0.0.1', 1252)


class Server:
    def __init__(self, addr):
        self.ip = addr[0]
        self.port = addr[1]
        self.conn = None
        self.pubkey = None
        self.rsaestablished = False

    def connect(self):
        if self.conn is None:
            self.conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.conn.connect((self.ip, self.port))

    def diconnect(self):
        if self.conn is not None:
            self.conn.close()
            self.conn = None


def createKeys(size):
    print('Generating RSA Keys')
    random_generator = Random.new().read
    key = RSA.generate(size, random_generator)
    print('Done')
    return key


def setupMsg(msg):
    data = f'{"MSG":<{4}}{len(msg):<{4}}'.encode('utf-8') + msg
    return data


def setupPubKey(key):
    data = f'{"PK":<{4}}{len(key):<{4}}'.encode('utf-8') + key
    return data


def receive():
    """Handles receiving of messages."""
    while True:
        full_msg = b''
        new_msg = True

        while 1:
            try:
                data = server.conn.recv(BUFFERSIZE)
            except:
                print(f'Connection Lost')
                server.conn = None
                break
            # If data is not empty
            if data:
                if new_msg:
                    msgtype = data[:3].decode('utf-8')  # Type of message (MSG/PK)
                    msglen = int(data[4:HEADERLEN].decode('utf-8'))  # Length of message
                    new_msg = False

                full_msg += data

                if len(full_msg) - HEADERLEN == msglen:

                    # Uncomment the following line to see raw messages
                    # print(str(full_msg))

                    # If message is a public key
                    if msgtype.strip(' ') == 'PK':
                        print(f'PubKey Recieved from server')
                        # Import public key string into RSA key object
                        srvpubkey = RSA.importKey(full_msg[HEADERLEN:])
                        encryptor = PKCS1_OAEP.new(srvpubkey)
                        server.pubkey = encryptor
                        print('Sending ENCTEST message to server')
                        server.conn.sendall(setupMsg(server.pubkey.encrypt('ENCTEST'.encode('utf-8'))))
                        server.conn.sendall(setupPubKey(pubkeybytes))

                    # If message is of MSG type
                    elif msgtype.strip(' ') == 'MSG':
                        decrypted = clidecryptor.decrypt(full_msg[HEADERLEN:]).decode('utf-8')

                        if server.rsaestablished is False:
                            if decrypted == 'ENCTEST':
                                server.rsaestablished = True
                                print(f'ENCTEST recieved from server')
                            else:
                                print(f'Server encryption test failed, Disconnecting')
                                server.disconnect()
                        else:
                            app.msglist.insert(tk.END, f'{decrypted}')
                            app.msglist.yview(tk.END)

                    new_msg = True
                    full_msg = b''




def exit_func():
    print("Exiting")
    try:
        server.diconnect()
    except:
        pass
    exit()


class GuiClient:
    def __init__(self, root):
        self.root = root
        self.builder = builder = pygubu.Builder()
        builder.add_resource_path(PROJECT_PATH)
        builder.add_from_file(PROJECT_UI)
        self.mainwindow = builder.get_object('frame_10')
        builder.connect_callbacks(self)

        self.root.bind('<Return>', self.SendMessage)

        self.msglist = builder.get_object('lstboxMsg')
        msgscroll = builder.get_object('scrollMsg')

        self.msgbox = builder.get_object('entryMessage')

        self.msglist.configure(yscrollcommand=msgscroll.set)
        msgscroll.configure(command=self.msglist.yview)

    def SendMessage(self, willy):
        content = tk.StringVar()
        content = self.msgbox.get()
        data = setupMsg(server.pubkey.encrypt(content.encode('utf-8')))
        self.msgbox.delete(0, tk.END)
        server.conn.send(data)
        self.msglist.insert(tk.END, "<You> " + content)

    def run(self):
        global pubkeybytes, clidecryptor, server
        key = createKeys(KEYSIZE)
        pubkey = key.publickey()
        # Clients public key in bytes string format
        pubkeybytes = pubkey.exportKey(format='PEM')

        # Decryptor to decrypt messages from the server
        clidecryptor = PKCS1_OAEP.new(key)

        server = Server(SERVER_ADDR)
        server.connect()

        atexit.register(exit_func)

        receive_thread = Thread(target=receive)
        receive_thread.setDaemon(True)
        receive_thread.start()
        self.mainwindow.mainloop()


if __name__ == '__main__':
    root = tk.Tk()
    app = GuiClient(root)
    app.run()
