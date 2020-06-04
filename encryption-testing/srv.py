import socket

from Cryptodome import Random
from Cryptodome.Cipher import PKCS1_OAEP
from Cryptodome.PublicKey import RSA

HEADERLEN = 12


def pubKeyPacket(data):
    data = f'{"PK":<{4}}{len(data):<{8}}'.encode('utf-8') + data
    return data


BINDADDR = ('127.0.0.1', 5555)
random_generator = Random.new().read

key = RSA.generate(1024, random_generator)

pubkey = key.publickey()

encryptor = PKCS1_OAEP.new(pubkey)

encrypted = encryptor.encrypt('test'.encode('utf-8'))

# print(f'Encrypted message: {encrypted}')

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.bind(BINDADDR)
sock.listen(64)

clisock, cliaddr = sock.accept()
print(f'conn from {cliaddr[0]}')

clisock.sendall(pubKeyPacket(pubkey.exportKey(format='PEM')))

clisock.close()
