import pytest
from Crypto.PublicKey import RSA
from mock import MagicMock

from encrypted_storage import (
    AESCipher,
    EncryptedSharedStorage,
    EncryptedRedisStorage,
    EncryptedSwiftStorage,
)

import swiftclient


def test_aes_cypher_by_passing_key():
    data = "Wow a wild data appeared."

    encrypt_cypher = AESCipher()
    encrypted = encrypt_cypher.encrypt(data)
    key = encrypt_cypher.key

    decrypt_cypher = AESCipher(key=key)
    decrypted = decrypt_cypher.decrypt(encrypted)
    assert data == decrypted


def test_aes_cypher_without_passing_key():
    data = "Wow a wild data appeared."

    cypher = AESCipher()
    encrypted = cypher.encrypt(data)
    decrypted = cypher.decrypt(encrypted)
    assert data == decrypted


def test_aes_cypher_with_key_shorter_than_blocksize():
    data = "Wow a wild data appeared."

    cypher = AESCipher(block_size=32)
    encrypted = cypher.encrypt(data)
    decrypted = cypher.decrypt(encrypted)
    assert data == decrypted


def test_encrypted_shared_storage():
    rsa_obj = RSA.generate(1024)
    private_key = rsa_obj.exportKey()
    public_key = rsa_obj.publickey().exportKey()

    data = "Wow a wild data appeared."

    cypher = EncryptedSharedStorage()
    encrypted_key, encrypted_data = cypher.asym_encryption(data, public_key)
    decrypted_data = cypher.asym_decryption(encrypted_key, encrypted_data,
                                            private_key)
    assert decrypted_data == data


@pytest.mark.xfail
def test_encrypted_redis_storage():
    rsa_obj = RSA.generate(1024)
    private_key = rsa_obj.exportKey()
    public_key = rsa_obj.publickey().exportKey()

    data = "Wow a wild data appeared."
    filename = "Just a filename"

    storage = EncryptedRedisStorage(db_num=10)
    storage.save(filename, data, public_key)
    loaded_data = storage.load(filename, private_key)

    assert loaded_data == data


@pytest.mark.xfail
def test_encrypted_swift_storage(monkeypatch):
    swift = MagicMock()
    monkeypatch.setattr(swiftclient.client, "Connection",
                        lambda **kwargs: swift)
    rsa_obj = RSA.generate(1024)
    private_key = rsa_obj.exportKey()
    public_key = rsa_obj.publickey().exportKey()

    data = "Wow a wild data appeared."
    filename = "Just a filename"
    container = "ooh_container"
    key_name = "key-" + filename
    data_name = "data-" + filename

    cypher = EncryptedSharedStorage()
    encrypted_key, encrypted_data = cypher.asym_encryption(data, public_key)

    monkeypatch.setattr(swift, 'get_object', lambda container, key_name: (None, encrypted_key))
    monkeypatch.setattr(swift, 'get_object', lambda container, data_name: (None, encrypted_data))

    storage = EncryptedSwiftStorage('ooh_container')
    storage.save(filename, data, public_key)
    loaded_data = storage.load(filename, private_key)

    assert loaded_data == data
