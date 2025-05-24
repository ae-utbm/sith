import functools
import hashlib
import uuid

from django.contrib.auth.hashers import BasePasswordHasher
from django.utils.crypto import constant_time_compare


class Sha256ApiKeyHasher(BasePasswordHasher):
    """
    An API key hasher using the sha256 algorithm.

    This hasher shouldn't be used in Django's `PASSWORD_HASHERS` setting.
    It is insecure for use in hashing passwords, but is safe for hashing
    high entropy, randomly generated API keys.
    """

    algorithm = "sha256"

    def salt(self) -> str:
        # No need for a salt on a high entropy key.
        return ""

    def encode(self, password: str, salt: str = "") -> str:
        hashed = hashlib.sha256(password.encode()).hexdigest()
        return f"{self.algorithm}$${hashed}"

    def verify(self, password: str, encoded: str) -> bool:
        encoded_2 = self.encode(password, "")
        return constant_time_compare(encoded, encoded_2)


@functools.cache
def get_hasher():
    return Sha256ApiKeyHasher()


def generate_key() -> tuple[str, str]:
    """Generate a [key, hash] couple."""
    key = str(uuid.uuid4())
    hasher = get_hasher()
    return key, hasher.encode(key)
