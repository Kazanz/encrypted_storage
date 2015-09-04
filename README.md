Encrypted Storage
=================
Encrypted Storage helps with saving and loading encrypted data in various storage backends.  It is implemented in a way to be able to add new backends easily by inheritance.

## How it works
It does AES symetric encyrption of a file, then asymetric RSA encryption on the key from the intial symetric encryption.  These files are then saved in one of the various storage backends.

## Currently implemented backends
- OpenStack Swift
- Redis

Installation
============

`pip install encrypted-storage`

Usage
=====

```python
from encrypted_storage import EncryptedRedisStorage

# Initialize storage.
storage = EncryptedRedisStorage(db_num=10)

# Encrypt and save data.
storage.save(filename, data, public_key)

# Decrypt and load data.
loaded_data = storage.load(filename, private_key)
```

## Backends

OpenStackSwift
`storage = EncryptedSwiftStorage(container='credit_card_data')`

Redis
`storage = EncryptedRedisStorage(db_num=10)`

Creating New RSA Keys
=====================
You can use whatever method you like to create new keys.  Just be sure the format is identical to the format of currently stored keys.  I recommend using Pycrypto to generate new keys as the encryption and encryption is based off of this package.  **Watch out for newlines if you copy and paste.**

```python
from Crypto.PublicKey import RSA
 
rsa_obj = RSA.generate(1024)
private_key = rsa_obj.exportKey()
public_key = rsa_obj.publickey().exportKey()
```

Adding New Storage Backends
===========================

To create new storage backends simply follow these 2 steps:

1. Create a class that inherits from `BaseSharedStorage`.  This will do the saving and loading from your storage.  If you wanted to create a new MongoDB storage backend you would write your own `MongoDBStorage` class with `save` and `load` functions specific to MongoDB.

```python
class MongoDBStorage(BaseSharedStorage):
    def __init__(self, myarg):
        # You can do init stuff here, like initializing your `pymongo.MongoClient`.
        self.mongo = pymongo.MongoClient()
        
    def save(self, filename, key, data):
        # do the MongoDB saving
        
    def load(self, filename):
        # do the MongoDB loading
```

2. Then you would write a new `EncryptedMongoDBStorage class that would inherit from your MongoDBStorage class and the EncryptedSharedStorage class.

```python 
class EncryptedMongoDBStorage(EncryptedSharedStorage, MongoDBStorage):
    def __init__(self, myarg):
        super(EncryptedMongoDBStorage, self).__init__(myarg)
```

## Rules
1. Your new storage backend save function must always accept a filename, key, and data in that order.
2. Your new storage backend load function must always accept a filename.
    
    
Encryption w/o Storage
======================

Sometimes you just want to encrypt stuff.

```python
from encrypted_storage import AESCypher, EncryptedSharedStorage
 
data = "These aren't the droids you are looking for."
 
# For symetrical encryption
encrypt_cypher = AESCipher()
encrypted = encrypt_cypher.encrypt(data)
key = encrypt_cypher.key
 
decrypt_cypher = AESCipher(key=key)
decrypted = decrypt_cypher.decrypt(encrypted)
 
 
# For asymetrical encryption
cypher = EncryptedSharedStorage()
encrypted_key, encrypted_data = cypher.asym_encryption(data, public_key)
decrypted_data = cypher.asym_decryption(encrypted_key, encrypted_data, private_key)
```

Contributing
============

If there is a backend you want that is not here, write one and open a pull request.

## Rules
1. Follow Pep8
2. Write Tests
3. Add yourself to list of contributors.

TODO
====

Create docker images with docker-compose for the different backends for testing.
