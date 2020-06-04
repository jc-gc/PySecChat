"""Script for Tkinter GUI chat client."""
from socket import AF_INET, socket, SOCK_STREAM, SHUT_RDWR
from threading import Thread
import tkinter
import atexit


def receive():
    """Handles receiving of messages."""
    while True:
        full_msg = ''
        new_msg = True
        while True:
            try:
                msg = client_socket.recv(32)
                if new_msg:
                    # print("new msg len:",msg[:HEADERSIZE])
                    msglen = int(msg[:3])
                    SENDERNAME = msg[4:HEADERSIZE].decode('utf-8')
                    SENDERNAME = "<" + SENDERNAME.strip(' ') + "> "

                    new_msg = False

                full_msg += msg.decode("utf-8")

                if len(full_msg) - HEADERSIZE == msglen:
                    # print("full msg recvd")
                    msg_list.insert(tkinter.END, SENDERNAME + full_msg[HEADERSIZE:])
                    new_msg = True
                    full_msg = ''

            except OSError:  # Possibly client has left the chat.
                break
        print("Exiting thread")


def send(event=None):
    """Handles sending of messages."""
    msg = my_msg.get()
    msg = add_header(msg)
    my_msg.set("")
    client_socket.send(bytes(msg, "utf8"))
    msg_list.insert(tkinter.END, "<Me> " + msg[HEADERSIZE:])

    if msg == "{quit}":
        client_socket.close()
        top.quit()


def add_header(message):
    msg = f'{len(message):<{3}} {NAME:<{HEADERSIZE - 4}}' + message
    return msg


def exit_func():
    print("Exiting")
    try:
        client_socket.close()
    except:
        pass
    exit()


top = tkinter.Tk()
top.title("Sexy Chat Room")

messages_frame = tkinter.Frame(top)
my_msg = tkinter.StringVar()  # For the messages to be sent.
my_msg.set("")
scrollbar = tkinter.Scrollbar(messages_frame)  # To navigate through past messages.
# Following will contain the messages.
msg_list = tkinter.Listbox(messages_frame, height=15, width=50, yscrollcommand=scrollbar.set)
scrollbar.pack(side=tkinter.RIGHT, fill=tkinter.Y)
msg_list.pack(side=tkinter.LEFT, fill=tkinter.BOTH)
msg_list.pack()
messages_frame.pack()

entry_field = tkinter.Entry(top, textvariable=my_msg)
entry_field.bind("<Return>", send)
entry_field.pack()
send_button = tkinter.Button(top, text="Send", command=send)
send_button.pack()

exit_button = tkinter.Button(top, text="Exit", command=top.destroy)
exit_button.pack()

top.protocol("WM_DELETE_WINDOW", top.destroy)

# ----Now comes the sockets part----
# HOST = input('Enter host: ')
# PORT = input('Enter port: ')
HOST = "2.25.19.181"
PORT = 1252
# NAME = input("Enter your username")
NAME = "pu55y boi"
if not PORT:
    PORT = 33000
else:
    PORT = int(PORT)

BUFSIZ = 1024
HEADERSIZE = 16
ADDR = (HOST, PORT)

client_socket = socket(AF_INET, SOCK_STREAM)
client_socket.connect(ADDR)

"""
while True:
    data = client_socket.recv(32)
    if data:
        print(data.decode('utf-8'))
"""

atexit.register(exit_func)

receive_thread = Thread(target=receive)
receive_thread.setDaemon(True)
receive_thread.start()
tkinter.mainloop()  # Starts GUI execution.
# exit_func()