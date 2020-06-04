import datetime
import socket
import threading
import time

HEADERLEN = 16
NAME = 'Server'
ENCODING = 'utf-8'
BUFFERSIZE = 64

# 0.0.0.0 will bind the server to all network interfaces
addr = ('0.0.0.0', 1252)

# Array of clients connected to the server (clientsocket, clientaddress)
clients = []
# List of active threads
threads = list()

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.bind(addr)
sock.listen(64)


def setupMsg(message, name):
    msg = f'{len(message):<{3}} {name:<{12}}' + message
    msg = msg.encode(ENCODING)
    return msg


def handleclient(conn, cliaddr):
    print('Client connected from ' + cliaddr[0])

    # Announce new connection to all other clients
    for client in clients:
        if client[0] != conn:
            client[0].sendall(setupMsg(('Client connected from ' + cliaddr[0]), NAME))

    time.sleep(0.05)
    conn.sendall(setupMsg("Welcome to the server.", NAME))
    conn.sendall(setupMsg("The time is: " + str(datetime.datetime.now()), NAME))

    full_msg = ''
    new_msg = True

    while 1:
        try:
            data = conn.recv(BUFFERSIZE)
        except:
            print(f'Client {cliaddr[0]} disconnected.')
            for client in clients:
                if client[0] != conn:
                    client[0].sendall(setupMsg((f'Client {cliaddr[0]} disconnected.'), NAME))
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
            client[0].sendall(setupMsg(message, name))


def acceptConnections():
    while 1:
        clicon, cliaddr = sock.accept()
        clients.append((clicon, cliaddr))
        x = threading.Thread(target=handleclient, args=(clicon, cliaddr))
        threads.append(x)
        x.start()


x = threading.Thread(target=acceptConnections)
threads.append(x)
x.start()

print('Running')

while 1:
    msg = input()
    if msg == 'exit':
        for client in clients:
            client[0].close()
        sock.close()
        exit()
