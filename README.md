# Kylis kit

> some personal kits, some cool function :)

## Install and import

```bash
pip install git+https://github.com/erwinliyh/kylis_kit@main
```

```python
import Kkit
# or
from Kkit import <module>
```

## `Kkit.fundict` module

Have fun in some special customised python Dict!

1. Class `Kkit.fundict.NoneDict`

   Return None is a key does not in the Dict

   Example:

   ```python
   from Kkit import fundict
   a = fundict.NoneDict({"a":1, "b":2})
   a["c"] # None
   ```

2. Class `Kkit.fundict.AbbrDict`

   You can input abbreviated key to access value

   Example:

   ```python
   from Kkit import fundict
   a = fundict.AbbrDict({"abxx":1, "acxx":2, "adxx":{"bcxx": 10, "bdxx":20}})
   a["a"]        # raise AmbiguityError
   a["ab"]       # 1
   a["ac"]       # 2
   a["ad"]["bc"] # 10
   a["ad"]["bd"] # 20
   a["c"]        # raise KeyError
   ```

## `Kkit.encryption` module

encrypt or decrypt a string with a string key using [`cryptography.fernet`](https://github.com/pyca/cryptography).

1. Function `gen_key(pin:str)`

   Transform a string to legal type used as key in `fernet`

   *Parameters*:

   1. `pin`: the string used as key

   *Return*:

   Bytes key

2. Function `encrypt_string(string:str, key:bytes, encoding:str)`

   Encode a string by a string type key

   *Parameters*:

   1. `string`: the string to be encrypted
   2. `key`: encryption key
   3. `encoding`: encoding of the `string`

   *Return*:

   encrypted string

3. Function `decrypt_string(string:str, key:bytes, encoding:str)`

   Decode a string by a string type key

   *Parameters*:

   1. `string`: the string to be dncrypted
   2. `key`: encryption key
   3. `encoding`: encoding of the `string`

   *Return*:

   decrypted string

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

