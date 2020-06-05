import socket
import threading
from random import *

import playsound
from Cryptodome import Random
from Cryptodome.Cipher import PKCS1_OAEP
from Cryptodome.PublicKey import RSA

HEADERLEN = 8
NAME = f'cliCl-{randint(100, 999)}'
ENCODING = 'utf-8'
BUFFERSIZE = 64


class Server:
    def __init__(self, ip, port):
        self.ip = ip
        self.port = port
        self.conn = None
        self.rsaestablished = False

    def connect(self):
        if self.conn is None:
            self.conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.conn.connect((self.ip, self.port))

    def diconnect(self):
        if self.conn is not None:
            self.conn.close()
            self.conn = None


def setupMsg(msg):
    data = f'{"MSG":<{4}}{len(msg):<{4}}'.encode('utf-8') + msg
    return data


def setupPubKey(key):
    data = f'{"PK":<{4}}{len(key):<{4}}'.encode('utf-8') + key
    return data


def showmsg():
    full_msg = b''
    new_msg = True
    while 1:
        try:
            msg = server.conn.recv(BUFFERSIZE)
        except:
            print('Connection Lost.')
            exit()

        if msg:
            if new_msg:
                msgtype = msg.decode('utf-8')[:3]
                msglen = int(msg.decode('utf-8')[4:HEADERLEN])
                new_msg = False

            full_msg += msg

            if len(full_msg) - HEADERLEN == msglen:
                if msgtype.strip(' ') == 'PK':
                    print('PK Recieved: ' + full_msg.decode('utf-8')[HEADERLEN:])
                    srvpubkey = RSA.importKey(full_msg[HEADERLEN:])
                    encryptor = PKCS1_OAEP.new(srvpubkey)
                    server.conn.sendall(setupPubKey(pubkey))
                    server.conn.sendall(setupMsg(encryptor.encrypt('ENCTEST'.encode('utf-8'))))


                elif msgtype.strip(' ') == 'MSG':
                    print('MSG Recieved: ' + full_msg.decode('utf-8')[HEADERLEN:])
                playsound.playsound('bing.wav')
                new_msg = True
                full_msg = b''


def sendmsg():
    global NAME
    while 1:
        msg = input()
        if msg == '/exit':
            server.disconnect()
            exit()
        elif msg.startswith('/name'):
            try:
                if len(msg.split(' ')[1]) <= 12:
                    NAME = msg.split(' ')[1]
                else:
                    print('[ERROR] Name too long')
            except:
                continue
        else:
            server.conn.sendall(setupMsg(msg, NAME))


random_generator = Random.new().read

key = RSA.generate(1024, random_generator)

pubkey = key.publickey().exportKey(format='PEM')

# Use 127.0.0.1 to connect to server running on your own pc
server = Server('wolfyxk.amcrestddns.com', 1252)
server.connect()

showthread = threading.Thread(target=showmsg)
sendthread = threading.Thread(target=sendmsg)

showthread.start()
sendthread.start()
