"""Security utilities for the Алло project."""

from cryptography.fernet import Fernet


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
