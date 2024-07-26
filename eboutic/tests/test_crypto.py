#!/usr/bin/env python3
#
# Skia < skia AT libskia DOT so >
#
# Beerware licensed software - 2017
#

import base64
from pathlib import Path

import pytest
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.padding import PKCS1v15
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKey, RSAPublicKey
from cryptography.hazmat.primitives.hashes import SHA1
from cryptography.hazmat.primitives.serialization import (
    load_pem_private_key,
    load_pem_public_key,
)
from django.conf import settings


def test_signature_valid():
    """Test that data sent to the bank is correctly signed."""
    data = "Amount=400&BasketID=4000&Auto=42&Error=00000\n".encode("utf-8")

    # Sign
    key_dir = Path(settings.BASE_DIR) / "eboutic" / "tests"
    privkey: RSAPrivateKey = load_pem_private_key(
        (key_dir / "private_key.pem").read_bytes(), None
    )
    pubkey: RSAPublicKey = load_pem_public_key(
        (key_dir / "public_key.pem").read_bytes()
    )
    signature = privkey.sign(data, PKCS1v15(), SHA1())
    b64sig = base64.b64encode(signature)
    signature = base64.b64decode(b64sig)
    try:
        pubkey.verify(signature, data, PKCS1v15(), SHA1())
    except InvalidSignature:
        pytest.fail("Failed to validate signature")
