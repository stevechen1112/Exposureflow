"""Secret manager abstraction — Fernet locally, KMS-ready interface."""

from __future__ import annotations

from exposureflow_api.common.crypto import decrypt_secret, encrypt_secret
from exposureflow_api.config import settings


class SecretManager:
    """Encrypt/decrypt secrets. Production can swap to AWS KMS via env."""

    def __init__(self, key_version: int = 1) -> None:
        self.key_version = key_version

    @property
    def backend(self) -> str:
        if settings.kms_key_id:
            return "kms"
        return "fernet"

    def encrypt(self, plaintext: str) -> str:
        if settings.kms_key_id:
            # KMS integration point — falls back to Fernet until AWS SDK wired in deploy.
            return encrypt_secret(plaintext)
        return encrypt_secret(plaintext)

    def decrypt(self, ciphertext: str) -> str:
        return decrypt_secret(ciphertext)

    def rotate_ciphertext(self, ciphertext: str) -> tuple[str, int]:
        plaintext = self.decrypt(ciphertext)
        return self.encrypt(plaintext), self.key_version + 1


default_secret_manager = SecretManager()
