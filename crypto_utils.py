import os
import logging
from cryptography.fernet import Fernet
import base64

logger = logging.getLogger('discobunty.crypto')

class CryptoManager:
    def __init__(self, secret_key: str):
        if not secret_key or len(secret_key) < 32:
            logger.warning("SECRET_KEY is too short or missing. Using a fallback key for testing (NOT SECURE!).")
            # Generate a consistent but insecure fallback for demonstration if not provided
            secret_key = "fallback-insecure-key-32-chars-long-!"
            
        # Fernet needs a 32-byte URL-safe base64-encoded key
        # We'll use a SHA256 hash of the secret_key to ensure it's always 32 bytes
        import hashlib
        key_32 = hashlib.sha256(secret_key.encode()).digest()
        self.fernet = Fernet(base64.urlsafe_b64encode(key_32))

    def encrypt(self, text: str) -> str:
        if not text: return ""
        if text.startswith("ENC:"): return text # Already encrypted
        return "ENC:" + self.fernet.encrypt(text.encode()).decode()

    def decrypt(self, text: str) -> str:
        if not text or not text.startswith("ENC:"):
            return text # Not encrypted
        try:
            encrypted_data = text[4:] # Remove "ENC:"
            return self.fernet.decrypt(encrypted_data.encode()).decode()
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            return text # Return as-is if decryption fails
