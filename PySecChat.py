from Cryptodome import Random
from Cryptodome.PublicKey import RSA

HEADERLEN = 8


class PySecChat:
    def setupMsg(self, msg):
        data = f'{"MSG":<{4}}{len(msg):<{4}}'.encode('utf-8') + msg
        return data

    def setupPubKey(self, key):
        data = f'{"PK":<{4}}{len(key):<{4}}'.encode('utf-8') + key
        return data

    def createKeys(self, size):
        random_generator = Random.new().read
        key = RSA.generate(size, random_generator)
        return key
