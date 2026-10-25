import hashlib
import hmac
import secrets

from django.db import models

KEY_PREFIX_LABEL = "urs_"


def _hash_key(raw_key: str) -> str:
    # API keys are 256-bit random values, so a plain SHA-256 is appropriate
    # (slow password hashes are only needed for low-entropy secrets).
    return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()


class Client(models.Model):
    """An independent application (e-commerce site, reels app, ...) using the API.

    The raw API key is shown ONCE when generated and is never stored: only its
    SHA-256 hash and a short non-secret prefix (used for lookup) are saved.
    """

    name = models.CharField(max_length=150)
    key_prefix = models.CharField(max_length=32, unique=True, editable=False)
    key_hash = models.CharField(max_length=64, editable=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

    def set_new_api_key(self) -> str:
        """Generate a new key, store its hash, and return the raw key (show it once!).

        Does not call save(); the caller saves the instance.
        """
        while True:
            prefix = KEY_PREFIX_LABEL + secrets.token_hex(4)
            if not Client.objects.filter(key_prefix=prefix).exclude(pk=self.pk).exists():
                break
        raw_key = f"{prefix}.{secrets.token_urlsafe(32)}"
        self.key_prefix = prefix
        self.key_hash = _hash_key(raw_key)
        return raw_key

    @classmethod
    def create_with_key(cls, name: str):
        client = cls(name=name)
        raw_key = client.set_new_api_key()
        client.save()
        return client, raw_key

    @classmethod
    def authenticate_key(cls, raw_key: str):
        """Return the active Client for this raw key, or None."""
        if not raw_key or "." not in raw_key:
            return None
        prefix = raw_key.split(".", 1)[0]
        client = cls.objects.filter(key_prefix=prefix).first()
        if client is None or not client.is_active:
            return None
        if not hmac.compare_digest(client.key_hash, _hash_key(raw_key)):
            return None
        return client
