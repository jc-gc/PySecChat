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
# Size of RSA key to generate
KEYSIZE = 1024


class Server:
    def __init__(self, ip, port):
        self.ip = ip
        self.port = port
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


def showmsg():
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
                        print(f'<MSG>: {decrypted}')

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


key = createKeys(KEYSIZE)
pubkey = key.publickey()
# Clients public key in bytes string format
pubkeybytes = pubkey.exportKey(format='PEM')

# Decryptor to decrypt messages from the server
clidecryptor = PKCS1_OAEP.new(key)

# Use 127.0.0.1 to connect to server running on your own pc
server = Server('wolfyxk.amcrestddns.com', 1252)
server.connect()

showthread = threading.Thread(target=showmsg)
sendthread = threading.Thread(target=sendmsg)

showthread.start()
sendthread.start()
