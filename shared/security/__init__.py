"""Security utilities for the Алло project."""

import os
from functools import lru_cache

from cryptography.fernet import Fernet, InvalidToken

ENC_PREFIX = "enc:"


class FieldEncryption:
    """
    Шифрование чувствительных полей в БД.
    Используется для SIP-паролей, YClients API-ключей.
    """

    def __init__(self, key: bytes):
        self.cipher = Fernet(key)

    def encrypt(self, plaintext: str) -> str:
        return self.cipher.encrypt(plaintext.encode()).decode()

    def decrypt(self, ciphertext: str) -> str:
        return self.cipher.decrypt(ciphertext.encode()).decode()


@lru_cache(maxsize=1)
def get_field_encryption() -> FieldEncryption:
    """ENCRYPTION_KEY — Fernet-ключ (Fernet.generate_key()). Без него сервис не стартует."""
    key = os.getenv("ENCRYPTION_KEY", "")
    if not key:
        raise RuntimeError("ENCRYPTION_KEY is not set")
    try:
        return FieldEncryption(key.encode())
    except ValueError as e:
        raise RuntimeError("ENCRYPTION_KEY must be a valid Fernet key") from e


def encrypt_value(value: str | None) -> str | None:
    if value is None or value.startswith(ENC_PREFIX):
        return value
    return ENC_PREFIX + get_field_encryption().encrypt(value)


def decrypt_value(value: str | None) -> str | None:
    if value is None or not value.startswith(ENC_PREFIX):
        return value  # старые незашифрованные значения читаются как есть
    try:
        return get_field_encryption().decrypt(value[len(ENC_PREFIX):])
    except InvalidToken as e:
        raise RuntimeError("Cannot decrypt field: wrong ENCRYPTION_KEY") from e
