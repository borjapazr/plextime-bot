from base64 import b64decode, b64encode
from hashlib import md5
from typing import Union, cast

from Crypto import Random
from Crypto.Cipher import AES


class AESCipher:
    def __init__(self, key: str) -> None:
        self.bs = AES.block_size
        self.key = key.encode()

    def encrypt(self, message: str) -> bytes:
        salt = Random.new().read(8)
        key_iv = self.__bytes_to_key(self.key, salt, 32 + 16)
        key = key_iv[:32]
        iv = key_iv[32:]
        aes = AES.new(key, AES.MODE_CBC, iv)
        return b64encode(b"Salted__" + salt + aes.encrypt(self.__pad(message.encode())))

    def decrypt(self, encrypted: str) -> bytes:
        encrypted_decoded = b64decode(encrypted)
        assert encrypted_decoded[0:8] == b"Salted__"  # noqa: S101
        salt = encrypted_decoded[8:16]
        key_iv = self.__bytes_to_key(self.key, salt, 32 + 16)
        key = key_iv[:32]
        iv = key_iv[32:]
        aes = AES.new(key, AES.MODE_CBC, iv)
        return self.__unpad(aes.decrypt(encrypted_decoded[16:]))

    def __pad(self, data: bytes) -> bytes:
        length = self.bs - (len(data) % self.bs)
        return data + (chr(length) * length).encode()

    @staticmethod
    def __unpad(data: bytes) -> bytes:
        return data[: -(data[-1] if type(data[-1]) == int else ord(cast(Union[str, bytes], data[-1])))]

    @staticmethod
    def __bytes_to_key(data: bytes, salt: bytes, output: int = 48) -> bytes:
        data += salt
        key = md5(data).digest()
        final_key = key
        while len(final_key) < output:
            key = md5(key + data).digest()
            final_key += key
        return final_key[:output]
