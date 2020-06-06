#!/usr/bin/env python
"""Script for Tkinter GUI chat client."""
import atexit
import os
import socket
import time
import tkinter as tk
from threading import Thread

import pygubu
from Cryptodome import Random
from Cryptodome.Cipher import PKCS1_OAEP
from Cryptodome.PublicKey import RSA

PROJECT_PATH = os.path.dirname(__file__)
PROJECT_UI = PROJECT_PATH + "/chatclient.ui"

HEADERLEN = 8
ENCODING = 'utf-8'
BUFFERSIZE = 64
# Size of RSA key to generate
KEYSIZE = 1024


class GuiClient:
    def __init__(self, root):
        # Tk GUI init
        self.root = root
        self.builder = builder = pygubu.Builder()
        builder.add_resource_path(PROJECT_PATH)
        builder.add_from_file(PROJECT_UI)
        self.mainwindow = builder.get_object('frame_10')
        builder.connect_callbacks(self)

        # Bind enter key to btnSendClick function
        self.root.bind('<Return>', self.btnSendClick)

        self.msglist = builder.get_object('lstboxMsg')
        self.msgbox = builder.get_object('entryMessage')
        self.ipentry = builder.get_object('entryIP')
        self.portentry = builder.get_object('entryPort')
        self.btnDisconnect = builder.get_object('btnDisconnect')
        self.btnConnect = builder.get_object('btnConnect')
        self.btnSend = builder.get_object('btnSend')

        msgscroll = builder.get_object('scrollMsg')
        self.msglist.configure(yscrollcommand=msgscroll.set)
        msgscroll.configure(command=self.msglist.yview)

        self.key = self.createKeys(KEYSIZE)
        self.pubkeybytes = self.key.publickey().exportKey(format='PEM')
        self.clidecryptor = PKCS1_OAEP.new(self.key)

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

        def disconnect(self):
            if self.conn is not None:
                self.conn.close()
                self.conn = None

    def setupMsg(self, msg):
        data = f'{"MSG":<{4}}{len(msg):<{4}}'.encode('utf-8') + msg
        return data

    def setupPubKey(self, key):
        data = f'{"PK":<{4}}{len(key):<{4}}'.encode('utf-8') + key
        return data

    def createKeys(self, size):
        print('Generating RSA Keys')
        random_generator = Random.new().read
        key = RSA.generate(size, random_generator)
        print('Done')
        return key

    def receive(self):
        full_msg = b''
        new_msg = True
        while True:
            try:
                data = self.server.conn.recv(BUFFERSIZE)
            except:
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
                        self.server.pubkey = encryptor
                        print('Sending ENCTEST message to server')
                        self.server.conn.sendall(self.setupMsg(self.server.pubkey.encrypt('ENCTEST'.encode('utf-8'))))
                        time.sleep(0.5)
                        self.server.conn.sendall(self.setupPubKey(self.pubkeybytes))

                    # If message is of MSG type
                    elif msgtype.strip(' ') == 'MSG':
                        decrypted = self.clidecryptor.decrypt(full_msg[HEADERLEN:]).decode('utf-8')

                        if self.server.rsaestablished is False:
                            if decrypted == 'ENCTEST':
                                self.server.rsaestablished = True
                                print(f'ENCTEST recieved from server')
                                self.msgbox.config(state='normal')
                                self.btnSend.config(state='normal')

                            else:
                                print(f'Server encryption test failed, Disconnecting')
                                self.server.disconnect()
                        else:
                            self.msglist.insert(tk.END, f'{decrypted}')
                            self.msglist.yview(tk.END)

                    new_msg = True
                    full_msg = b''

    def btnSendClick(self, *args):
        content = str(app.msgbox.get())
        data = self.setupMsg(self.server.pubkey.encrypt(content.encode('utf-8')))
        self.msgbox.delete(0, tk.END)
        self.server.conn.send(data)
        self.msglist.insert(tk.END, "<You> " + content)

    def btnConnectClick(self):
        self.ipentry.config(state='disabled')
        self.portentry.config(state='disabled')
        self.btnConnect.config(state='disabled')
        try:
            ip = str(self.ipentry.get())
            port = int(self.portentry.get())
            addr = (ip, port)

            self.server = self.Server(addr)
            self.server.connect()

            self.receive_thread = Thread(target=self.receive)
            self.receive_thread.setDaemon(True)
            self.receive_thread.start()
            self.btnDisconnect.config(state='normal')
        except:
            self.ipentry.config(state='normal')
            self.portentry.config(state='normal')
            self.btnConnect.config(state='normal')
            self.msglist.insert(tk.END, 'Connection Failed')

    def btnDisconnectCLick(self):
        try:
            self.server.disconnect()
            self.server = None
            self.ipentry.config(state='normal')
            self.portentry.config(state='normal')
            self.btnConnect.config(state='normal')
            self.msgbox.config(state='disabled')
            self.btnSend.config(state='disabled')
            self.btnDisconnect.config(state='disabled')
            self.receive_thread = None
        except Exception as e:
            print(e)

    def exit_func(self):
        if self.server is not None:
            self.server.disconnect()

    def run(self):
        atexit.register(self.exit_func)
        self.mainwindow.mainloop()


if __name__ == '__main__':
    root = tk.Tk()
    app = GuiClient(root)
    app.run()
