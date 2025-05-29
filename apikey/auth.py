from django.http import HttpRequest
from ninja.security import APIKeyHeader

from apikey.hashers import get_hasher
from apikey.models import ApiClient, ApiKey


class ApiKeyAuth(APIKeyHeader):
    param_name = "X-APIKey"

    def authenticate(self, request: HttpRequest, key: str | None) -> ApiClient | None:
        if not key or len(key) != ApiKey.KEY_LENGTH:
            return None
        hasher = get_hasher()
        hashed_key = hasher.encode(key)
        try:
            key_obj = ApiKey.objects.get(revoked=False, hashed_key=hashed_key)
        except ApiKey.DoesNotExist:
            return None
        return key_obj.client
