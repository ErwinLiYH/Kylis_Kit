"""
This module provides functions to encrypt and decrypt strings simply.

Example:

```python
from Kkit import encryption
from cryptography.fernet import Fernet

# there are two ways to generate key:
key = Fernet.generate_key()           # generate key by Fernet
key = encryption.gen_key("your pin")  # generate key from a string

string_to_be_encrypted = "string_to_be_encrypted"
encrypted_string = encryption.encrypt_string(string_to_be_encrypted, key)
decrypted_string = decryption.encrypt_string(encrypted_string, key)
# decrypted_string will equal to string_to_be_encrypted
```
"""

import hashlib
import base64
from cryptography.fernet import Fernet

def gen_key(pin):
    """
    Generate a key that used in encryption and decryption from a string pin.

    Parameters
    ----------
    pin : str
        A string pin to generate a key.

    Returns
    -------
    bytes
        A key that can be used in encryption and decryption.
    """
    bytes_key = pin.encode('utf-8')
    hash_object = hashlib.sha256(bytes_key)
    hex_dig = hash_object.hexdigest()
    key_bytes = bytes.fromhex(hex_dig)[:32]
    key = base64.urlsafe_b64encode(key_bytes)
    return key

def encrypt_string(string, key, encoding="utf-8"):
    """
    Encrypt a string with a key.

    Parameters
    ----------
    string : str
        A string to be encrypted.

    key : bytes
        A key that used to encrypt the string.

    encoding : str
        The encoding of the string. Default is 'utf-8'.

    Returns
    -------
    str
        The encrypted string.
    """
    cipher_suite = Fernet(key)
    return cipher_suite.encrypt(string.encode(encoding)).decode(encoding)

def decrypt_string(string, key, encoding="utf-8"):
    """
    Decrypt a string with a key.

    Parameters
    ----------
    string: str
        A string to be decrypted.

    key: bytes
        A key that used to decrypt the string.
        
    encoding: str
        The encoding of the string. Default is 'utf-8'.

    Returns
    -------
    str
        The decrypted string.
    """
    cipher_suite = Fernet(key)
    return cipher_suite.decrypt(string.encode(encoding)).decode(encoding)
