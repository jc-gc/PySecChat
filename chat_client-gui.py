#!/usr/bin/env python
"""Script for Tkinter GUI chat client."""
import atexit
import socket
import tkinter
from random import randint
from threading import Thread

from Cryptodome import Random
from Cryptodome.Cipher import PKCS1_OAEP
from Cryptodome.PublicKey import RSA

HEADERLEN = 8
NAME = f'guiCl-{randint(100, 999)}'
ENCODING = 'utf-8'
BUFFERSIZE = 64
# Size of RSA key to generate
KEYSIZE = 1024

# Use 127.0.0.1 to connect to server running on your own pc
SERVER_ADDR = ('wolfyxk.amcrestddns.com', 1252)


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
                            msg_list.insert(tkinter.END, f'{decrypted}')
                            msg_list.yview(tkinter.END)

                    new_msg = True
                    full_msg = b''


def send(event=None):
    """Handles sending of messages."""
    msg = my_msg.get()
    data = setupMsg(server.pubkey.encrypt(msg.encode('utf-8')))
    my_msg.set("")
    server.conn.send(data)
    msg_list.insert(tkinter.END, "<You> " + msg)

    if msg == "{quit}":
        server.diconnect()
        top.quit()
    msg_list.yview(tkinter.END)


def change_name(event=None):
    name = my_msg.get()
    if len(name) > 12:
        msg_list.insert(tkinter.END, "Error: Name too long")
        return
    global NAME
    NAME = name
    msg_list.insert(tkinter.END, "Name change succesful")


def exit_func():
    print("Exiting")
    try:
        server.diconnect()
    except:
        pass
    exit()


top = tkinter.Tk()
top.title("Chat Room")

messages_frame = tkinter.Frame(top)
my_msg = tkinter.StringVar()  # For the messages to be sent.
my_msg.set("")
scrollbar = tkinter.Scrollbar(messages_frame)  # To navigate through past messages.
# Following will contain the messages.
msg_list = tkinter.Listbox(messages_frame, height=15, width=50, yscrollcommand=scrollbar.set)
scrollbar.configure(command=msg_list.yview)
scrollbar.pack(side=tkinter.RIGHT, fill=tkinter.Y)
msg_list.pack(side=tkinter.LEFT, fill=tkinter.BOTH)
msg_list.configure(yscrollcommand=scrollbar.set)

msg_list.pack()
messages_frame.pack()

entry_field = tkinter.Entry(top, textvariable=my_msg)
entry_field.bind("<Return>", send)
entry_field.pack()

send_button = tkinter.Button(top, text="Send", command=send)
send_button.pack()

send_button = tkinter.Button(top, text="Change Name", command=change_name)
send_button.pack()

exit_button = tkinter.Button(top, text="Exit", command=top.destroy)
exit_button.pack()

top.protocol("WM_DELETE_WINDOW", top.destroy)

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
tkinter.mainloop()  # Starts GUI execution.
