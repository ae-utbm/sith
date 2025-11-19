import functools
import hashlib
import secrets

from django.contrib.auth.hashers import BasePasswordHasher
from django.utils.crypto import constant_time_compare


class Sha512ApiKeyHasher(BasePasswordHasher):
    """
    An API key hasher using the sha512 algorithm.

    This hasher shouldn't be used in Django's `PASSWORD_HASHERS` setting.
    It is insecure for use in hashing passwords, but is safe for hashing
    high entropy, randomly generated API keys.
    """

    algorithm = "sha512"

    def salt(self) -> str:
        # No need for a salt on a high entropy key.
        return ""

    def encode(self, password: str, salt: str = "") -> str:
        hashed = hashlib.sha512(password.encode()).hexdigest()
        return f"{self.algorithm}$${hashed}"

    def verify(self, password: str, encoded: str) -> bool:
        encoded_2 = self.encode(password, "")
        return constant_time_compare(encoded, encoded_2)


@functools.cache
def get_hasher():
    return Sha512ApiKeyHasher()


def generate_key() -> tuple[str, str]:
    """Generate a [key, hash] couple."""
    # this will result in key with a length of 72
    key = str(secrets.token_urlsafe(54))
    hasher = get_hasher()
    return key, hasher.encode(key)
