import socket
import datetime
from _thread import *
import tkinter

ThreadCount = 0

HEADERLEN = 16
NAME = 'Server'

addr = ('0.0.0.0', 1252)

clients = []

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.bind(addr)
sock.listen(64)

def addheader(message, name):
    msg = f'{len(message):<{3}} {name:<{12}}' + message
    return msg

def handleclient(conn, cliaddr):
        print('Client connected from ' + cliaddr[0])
        for client in clients:
            if client[0] != conn:
                client[0].sendall(addheader(('Client connected from ' + cliaddr[0]),NAME).encode('utf-8'))
        conn.sendall(addheader("Welcome to the server.",NAME).encode('utf-8'))
        conn.sendall(addheader(("The time is: " + str(datetime.datetime.now())),NAME).encode('utf-8'))

        full_msg = ''
        new_msg = True
        while 1:
            try:
                data = conn.recv(32)
            except:
                print(f'Client {cliaddr[0]} disconnected.')
                for client in clients:
                    if client[0] != conn:
                        client[0].sendall(addheader((f'Client {cliaddr[0]} disconnected.'),NAME).encode('utf-8'))
                clients.remove((conn, cliaddr))
                break
            if data:
                if new_msg:
                    msglen = int(data[:3])
                    sendername = data[4:HEADERLEN].decode('utf-8')
                    new_msg = False

                full_msg += data.decode("utf-8")

                if len(full_msg) - HEADERLEN == msglen:
                    print(f'<{cliaddr[0]}> {sendername.strip(" ")}: {full_msg[HEADERLEN:]}')
                    broadcast((conn, cliaddr), full_msg[HEADERLEN:], sendername)
                    new_msg = True
                    full_msg = ''


def broadcast(source, message, name):
    for client in clients:
        if client[0] != source[0]:
            client[0].sendall(addheader(message, name).encode('utf-8'))

while 1:
    clicon, cliaddr = sock.accept()
    clients.append((clicon, cliaddr))
    start_new_thread(handleclient, (clicon, cliaddr))
    ThreadCount += 1