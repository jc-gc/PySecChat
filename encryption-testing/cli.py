import socket

HEADERLEN = 12

SERVERADDR = ('127.0.0.1', 5555)

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect(SERVERADDR)

new_msg = True
full_msg = b''

while 1:
    try:
        data = sock.recv(128)
    except:
        sock.close()
        exit()
    if data:
        if new_msg:
            msgtype = data[:3]
            msglen = int(data[4:HEADERLEN])
            new_msg = False

        full_msg += data

        if len(full_msg) - HEADERLEN == msglen:
            print(full_msg[HEADERLEN:])
            new_msg = True
            full_msg = ''
