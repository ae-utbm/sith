#!/usr/bin/env python3
# -*- coding:utf-8 -*
#
# Skia < skia AT libskia DOT so >
#
# Beerware licensed software - 2017
#

import base64

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.padding import PKCS1v15
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKey
from cryptography.hazmat.primitives.hashes import SHA1
from cryptography.hazmat.primitives.serialization import (
    load_pem_private_key,
    load_pem_public_key,
)

with open("./private_key.pem", "br") as f:
    PRIVKEY = f.read()
with open("./public_key.pem", "br") as f:
    PUBKEY = f.read()

data = "Amount=400&BasketID=4000&Auto=42&Error=00000\n".encode("utf-8")

# Sign
privkey: RSAPrivateKey = load_pem_private_key(PRIVKEY, None)
signature = privkey.sign(data, PKCS1v15(), SHA1())
b64sig = base64.b64encode(signature)
print(b64sig)

# Verify
pubkey = load_pem_public_key(PUBKEY)
signature = base64.b64decode(b64sig)
try:
    pubkey.verify(signature, data, PKCS1v15(), SHA1())
    print("Verify OK")
except InvalidSignature as e:
    print("Verify failed")
