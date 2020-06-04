"""Script for Tkinter GUI chat client."""
import atexit
import tkinter
import select
from random import randint
from socket import AF_INET, socket, SOCK_STREAM, IPPROTO_TCP, SOL_SOCKET, SO_KEEPALIVE, TCP_KEEPIDLE, TCP_KEEPINTVL, TCP_KEEPCNT
from threading import Thread


HEADERLEN = 16
NAME = f'guiCl-{randint(100, 999)}'
ENCODING = 'utf-8'
BUFFERSIZE = 64

SERVER_ADDR = ('wolfyxk.amcrestddns.com', 1252)


def receive():
    """Handles receiving of messages."""
    while True:
        full_msg = ''
        new_msg = True
        while True:
            try:
                msg = client_socket.recv(BUFFERSIZE)
                
                if new_msg == True and msg.decode("utf-8") == "":
                    print("Connection Ended")
                    break
                
                if new_msg:
                    msglen = int(msg[:3])
                    sendername = msg[4:HEADERLEN].decode('utf-8')
                    sendername = "<" + sendername.strip(' ') + "> "

                    new_msg = False

                full_msg += msg.decode("utf-8")

                if len(full_msg) - HEADERLEN == msglen:
                    msg_list.insert(tkinter.END, sendername + full_msg[HEADERLEN:])
                    msg_list.yview(tkinter.END)
                    new_msg = True
                    full_msg = ''

            except OSError:  # Possibly client has left the chat.
                print("OSError")
                break
        print("Exiting thread")
        break
    top.destroy()
    exit()


def send(event=None):
    """Handles sending of messages."""
    msg = my_msg.get()
    msgenc = setupMsg(msg, NAME)
    my_msg.set("")
    client_socket.send(msgenc)
    msg_list.insert(tkinter.END, "<You> " + msg)

    if msg == "{quit}":
        client_socket.close()
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


def setupMsg(message, name):
    msg = f'{len(message):<{3}} {name:<{12}}' + message
    msg = msg.encode(ENCODING)
    return msg


def exit_func():
    print("Exiting")
    try:
        client_socket.close()
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

client_socket = socket(AF_INET, SOCK_STREAM)
client_socket.setsockopt(SOL_SOCKET, SO_KEEPALIVE, 1)
after_idle_sec=1
interval_sec=3
max_fails=5
client_socket.setsockopt(IPPROTO_TCP, TCP_KEEPIDLE, after_idle_sec)
client_socket.setsockopt(IPPROTO_TCP, TCP_KEEPINTVL, interval_sec)
client_socket.setsockopt(IPPROTO_TCP, TCP_KEEPCNT, max_fails)
try:
    client_socket.connect(SERVER_ADDR)
except:
    print("No connection found")
    exit()
atexit.register(exit_func)

receive_thread = Thread(target=receive)
receive_thread.setDaemon(True)
receive_thread.start()
tkinter.mainloop()  # Starts GUI execution.
