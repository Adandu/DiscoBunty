import base64
from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import os
import logging
import hashlib

logger = logging.getLogger('discobunty.crypto')

# Fixed application salt — not secret, just prevents generic rainbow tables.
APP_SALT = b'bunty_static_salt_2024'
# Changing this invalidates all existing encrypted config values.
_PBKDF2_ITERATIONS = 100_000


class CryptoManager:
    def __init__(self, secret_key: str):
        if not secret_key or len(secret_key) < 32:
            msg = "CRITICAL: SECRET_KEY is missing or too short (min 32 chars). Application cannot start safely."
            logger.error(msg)
            raise ValueError(msg)

        # Primary key: PBKDF2-derived (100k iterations — resistant to brute-force)
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=APP_SALT,
            iterations=_PBKDF2_ITERATIONS,
        )
        key_bytes = kdf.derive(secret_key.encode())
        self.fernet = Fernet(base64.urlsafe_b64encode(key_bytes))

        # Legacy key: SHA256-derived — only used to decrypt values encrypted before v2.
        # Remove after all config files have been re-saved with the new KDF.
        legacy_key_bytes = hashlib.sha256(secret_key.encode()).digest()
        self._legacy_fernet = Fernet(base64.urlsafe_b64encode(legacy_key_bytes))

    def encrypt(self, text: str) -> str:
        if not text:
            return ""
        if text.startswith("ENC:"):
            return text  # Already encrypted
        return "ENC:" + self.fernet.encrypt(text.encode()).decode()

    def decrypt(self, text: str) -> str:
        if not text or not text.startswith("ENC:"):
            return text  # Not encrypted / plaintext
        encrypted_data = text[4:]  # Strip "ENC:" prefix
        try:
            return self.fernet.decrypt(encrypted_data.encode()).decode()
        except InvalidToken:
            # Value was encrypted with the old SHA256 key — migrate transparently
            try:
                plaintext = self._legacy_fernet.decrypt(encrypted_data.encode()).decode()
                logger.warning("Decrypted value using legacy SHA256 key — security upgrade required (re-save config to use PBKDF2).")
                return plaintext
            except Exception as e:
                logger.error(f"Decryption failed with both primary and legacy key: {e}")
                return text  # Return ciphertext as-is rather than crash
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            return text
