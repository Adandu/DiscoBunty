import base64
import hashlib
import hmac
import secrets

PASSWORD_HASH_PREFIX = "PBKDF2_SHA256"
PASSWORD_HASH_ITERATIONS = 310_000


def is_password_hash(value: str) -> bool:
    return bool(value and value.startswith(f"{PASSWORD_HASH_PREFIX}$"))


def hash_password(password: str) -> str:
    if not password:
        return ""
    if is_password_hash(password):
        return password

    salt = secrets.token_bytes(16)
    derived = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        PASSWORD_HASH_ITERATIONS,
    )
    salt_b64 = base64.urlsafe_b64encode(salt).decode("ascii")
    digest_b64 = base64.urlsafe_b64encode(derived).decode("ascii")
    return f"{PASSWORD_HASH_PREFIX}${PASSWORD_HASH_ITERATIONS}${salt_b64}${digest_b64}"


def verify_password(candidate: str, stored_value: str) -> bool:
    if not candidate or not stored_value:
        return False

    if not is_password_hash(stored_value):
        return hmac.compare_digest(candidate, stored_value)

    try:
        _, iterations, salt_b64, digest_b64 = stored_value.split("$", 3)
        salt = base64.urlsafe_b64decode(salt_b64.encode("ascii"))
        expected = base64.urlsafe_b64decode(digest_b64.encode("ascii"))
        actual = hashlib.pbkdf2_hmac(
            "sha256",
            candidate.encode("utf-8"),
            salt,
            int(iterations),
        )
        return hmac.compare_digest(actual, expected)
    except Exception:
        return False
