import socket
import threading
from random import *

import playsound

HEADERLEN = 16
NAME = f'cliCl-{randint(100, 999)}'
ENCODING = 'utf-8'
BUFFERSIZE = 64

# Use 127.0.0.1 to connect to server running on your own pc
server = ('127.0.0.1', 1252)

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect(server)


def setupMsg(message, name):
    msg = f'{len(message):<{3}} {name:<{12}}' + message
    msg = msg.encode(ENCODING)
    return msg


def showmsg():
    full_msg = ''
    new_msg = True
    while 1:
        try:
            msg = sock.recv(BUFFERSIZE)
        except:
            print('Connection Lost.')
            exit()

        if msg:
            if new_msg:
                msglen = int(msg[:3])
                sendername = msg[4:HEADERLEN].decode('utf-8')
                new_msg = False

            full_msg += msg.decode("utf-8")

            if len(full_msg) - HEADERLEN == msglen:
                print(sendername.strip(' ') + ': ' + full_msg[HEADERLEN:])
                playsound.playsound('bing.wav')
                new_msg = True
                full_msg = ''


def sendmsg():
    global NAME
    while 1:
        msg = input()
        if msg == '/exit':
            sock.close()
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
            sock.sendall(setupMsg(msg, NAME))


showthread = threading.Thread(target=showmsg)
sendthread = threading.Thread(target=sendmsg)

showthread.start()
sendthread.start()
