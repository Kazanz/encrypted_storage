"""
See README for how to create new backends, add keys, store keys, and basic
usage instruction.
"""
import base64
import logging
import requests
from Crypto import Random
from Crypto.Cipher import AES
from Crypto.PublicKey import RSA
import Crypto.Random.OSRNG.posix as RNG

from redis import StrictRedis
import swiftclient

logger = logging.getLogger(__name__)


__all__ = ["generate_key", "AESCipher", "BaseSharedStorage",
           "EncryptedSharedStorage", "RedisStorage", "EncryptedRedisStorage",
           "SwiftStorage", "EncryptedSwiftStorage"]


def generate_key(key_size=32):
    """Take an int and return a random key the size of the int."""
    return RNG.new().read(key_size)


class AESCipher:
    """Object for symetrical encrypting and decrypting."""
    def __init__(self, key=False, block_size=32):
        if not key:
            key = generate_key()
        self.bs = block_size
        if len(key) >= block_size:
            self.key = key[:block_size]
        else:
            self.key = self._pad(key)

    def encrypt(self, raw):
        """Takes raw data returns encrypted data base64 encoded."""
        raw = self._pad(raw)
        iv = Random.new().read(AES.block_size)
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        return base64.b64encode(iv + cipher.encrypt(raw))

    def decrypt(self, enc, key=False):
        """Takes base64 encoded cipher text (and a key if provided)
        then returns decrypted data base64 decoded."""
        enc = base64.b64decode(enc)
        iv = enc[:AES.block_size]
        if not key:
            key = self.key
        cipher = AES.new(self._assure_proper_key_length(key), AES.MODE_CBC, iv)
        return self._unpad(cipher.decrypt(enc[AES.block_size:]))

    def _assure_proper_key_length(self, key):
        if len(key) < 32:
            for unused_i in range(0, 32-len(key)):
                key = '\x00' + key
        return key

    def _pad(self, s):
        """Add padding via Voodoo magic."""
        return s + (self.bs - len(s) % self.bs) * chr(self.bs - len(s) % self.bs)

    def _unpad(self, s):
        """Remove padding by more powerful Voodoo magic."""
        return s[:-ord(s[len(s)-1:])]


class BaseSharedStorage(object):
    def __init__(self, **kwargs):
        self.settings = kwargs
        return super(BaseSharedStorage, self).__init__()

    def save(self, name, encrypted_key, encrypted_data):
        raise NotImplementedError

    def load(self, name):
        raise NotImplementedError


class EncryptedSharedStorage(BaseSharedStorage):
    def save(self, filename, data, public_key):
        encrypted_key, encrypted_data = self.asym_encryption(data, public_key)
        super(EncryptedSharedStorage, self).save(filename, encrypted_key,
                                                 encrypted_data)

    def load(self, filename, private_key):
        encrypted_key, encrypted_data = super(EncryptedSharedStorage,
                                              self).load(filename)
        return self.asym_decryption(encrypted_key, encrypted_data, private_key)

    def asym_encryption(self, data, public_key):
        key, encrypted_data = self._sym_encrypt(data)
        encrypted_key = self._asym_encrypt(key, public_key)
        return encrypted_key, encrypted_data

    def asym_decryption(self, encrypted_key, encrypted_data, private_key):
        decrypted_key = self._asym_decrypt(encrypted_key, private_key)
        return self._sym_decrypt(decrypted_key, encrypted_data)

    def _sym_encrypt(self, data):
        """Encrpyt data and return key and cipher text."""
        cipher = AESCipher()
        cipher_text = cipher.encrypt(data)
        return cipher.key, cipher_text

    def _sym_decrypt(self, key, data):
        """Take a key and cipher text return decrypted data."""
        cipher = AESCipher()
        return cipher.decrypt(data, key)

    def _asym_encrypt(self, data, public_key):
        """Encrpyt data using the public key."""
        key = RSA.importKey(public_key)
        encrypted_key = key.encrypt(data, None)
        return encrypted_key[0]

    def _asym_decrypt(self, data, private_key):
        """Decrypt the data with the given private key."""
        key = RSA.importKey(private_key)
        return key.decrypt(data)

    def dummy_load_data(self, data="Dummy"):
        """Used to return dummy data when a process fails in a backend loading
        function so the entire process doesn't break."""
        key, encrypted_data = self._sym_encrypt(data)
        encrypted_key = self._asym_encrypt(key, self.settings['PRIVATE_KEY'])
        return encrypted_key, encrypted_data


class RedisStorage(BaseSharedStorage):
    def __init__(self, db_num):
        self._redis = StrictRedis(db=db_num)

    def save(self, filename, key, data):
        self._purge_duplicates(filename)
        self._redis.hset(filename, key, data)

    def load(self, filename):
        redis_keys = self._redis.hkeys(filename)
        key = redis_keys[0]  # Should never be more than one key
        data = self._redis.hget(filename, key)
        return key, data

    def _purge_duplicates(self, dict_key):
        """Remove identical files from server to be replaced by new files."""
        keys = self._redis.hkeys(dict_key)
        for key in keys:
            self._redis.hdel(dict_key, key)


class SwiftStorage(BaseSharedStorage):
    """To use OpenStack Swift storage be sure to create the container
    before trying to save or load from it.

    Your settings must contain these variables:
    SWIFT_AUTH_URL, SWIFT_KEY, SWIFT_USER.
    """
    def __init__(self, container, insecure=True):
        self.swift = swiftclient.client.Connection(
            authurl=self.settings['SWIFT_AUTH_URL'],
            user=self.settings['SWIFT_USER'],
            key=self.settings['SWIFT_KEY'],
            insecure=insecure,
        )
        self.container = container
        self.key_leader = "key-"
        self.data_leader = "data-"
        self.exceptions = (
            requests.exceptions.ConnectionError,
            swiftclient.exceptions.ClientException,
        )

    def save(self, filename, key, data):
        key_name, data_name = self._get_names(filename)
        try:
            self.swift.put_object(self.container, key_name, key)
            self.swift.put_object(self.container, data_name, data)
        except self.exceptions:
            logger.exception('Swift was unable to "Save".')

    def load(self, filename):
        key_name, data_name = self._get_names(filename)
        try:
            key = self.swift.get_object(self.container, key_name)[-1]
            data = self.swift.get_object(self.container, data_name)[-1]
        except self.exceptions:
            logger.info('Swift was unable to "Load" filename %s.', filename)
            return self.dummy_load_data()
        return key, data

    def _get_names(self, filename):
        """Prepends key and data identifiers to front of filename."""
        key_name = self.key_leader + str(filename)
        data_name = self.data_leader + str(filename)
        return key_name, data_name


class EncryptedRedisStorage(EncryptedSharedStorage, RedisStorage):
    def __init__(self, db_num):
        super(EncryptedRedisStorage, self).__init__(db_num)
    """
    Init with the db number for redis.
    When calling save() | .save(filename, data, public_key).
    When calling load() | .load(filename, private_key).
    Duplicate filenames are always overwritten.
    """
    pass


class EncryptedSwiftStorage(EncryptedSharedStorage, SwiftStorage):
    def __init__(self, container, insecure=True):
        super(EncryptedSwiftStorage, self).__init__(container, insecure)
    """
    Init with the container_name for swift.
    Insecure kwarg defaults to True.
    When calling save() | .save(filename, data, public_key).
    When calling load() | .load(filename, private_key).
    Duplicate filenames are always overwritten.
    """
    pass
