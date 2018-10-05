#!/usr/bin/env python3
# -*- coding:utf-8 -*
#
# Skia < skia AT libskia DOT so >
#
# Beerware licensed software - 2017
#

import base64
from OpenSSL import crypto

with open("./private_key.pem") as f:
    PRVKEY = f.read()
with open("./public_key.pem") as f:
    PUBKEY = f.read()

string = "Amount=400&BasketID=4000&Auto=42&Error=00000\n"

# Sign
prvkey = crypto.load_privatekey(crypto.FILETYPE_PEM, PRVKEY)
sig = crypto.sign(prvkey, string, "sha1")
b64sig = base64.b64encode(sig)
print(b64sig)

# Verify
pubkey = crypto.load_publickey(crypto.FILETYPE_PEM, PUBKEY)
cert = crypto.X509()
cert.set_pubkey(pubkey)
sig = base64.b64decode(b64sig)
try:
    crypto.verify(cert, sig, string, "sha1")
    print("Verify OK")
except:
    print("Verify failed")
