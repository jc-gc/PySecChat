import datetime
import socket
import atexit
import threading
import time

HEADERSIZE = 16

server = ('2.25.19.181', 1252)

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect(server)

NAME = 'CSI'

RUN = True

def addheader(message, name):
    msg = f'{len(message):<{3}} {name:<{12}}' + message
    return msg

def exithandle():
    sock.close()

atexit.register(exithandle)

def showmsg():
    global RUN
    full_msg = ''
    new_msg = True
    while RUN:
        msg = sock.recv(64)
        if new_msg:
            msglen = int(msg[:3])
            sendername = msg[4:HEADERSIZE].decode('utf-8')
            new_msg = False

        full_msg += msg.decode("utf-8")

        if len(full_msg) - HEADERSIZE == msglen:
            print(sendername.strip(' ') + ': ' + full_msg[HEADERSIZE:])
            new_msg = True
            full_msg = ''

def sendmsg():
    global RUN
    while RUN:
        msg = input()
        if msg == 'exit':
            RUN = False
        sock.sendall(addheader(msg,NAME).encode('utf-8'))

showthread = threading.Thread(target=showmsg)
sendthread = threading.Thread(target=sendmsg)

showthread.start()
sendthread.start()