import hashlib
import base64
from cryptography.fernet import Fernet

def gen_key(pin):
    bytes_key = pin.encode('utf-8')
    hash_object = hashlib.sha256(bytes_key)
    hex_dig = hash_object.hexdigest()
    key_bytes = bytes.fromhex(hex_dig)[:32]
    key = base64.urlsafe_b64encode(key_bytes)
    return key

def encrypt_string(string, key, encoding="utf-8"):
    # key = gen_key(key)
    cipher_suite = Fernet(key)
    return cipher_suite.encrypt(string.encode(encoding)).decode(encoding)

def decrypt_string(string, key, encoding="utf-8"):
    # key = gen_key(key)
    cipher_suite = Fernet(key)
    return cipher_suite.decrypt(string.encode(encoding)).decode(encoding)
