import unittest

from auth_utils import hash_password, is_password_hash, verify_password


class AuthUtilsTests(unittest.TestCase):
    def test_hash_password_creates_verifiable_hash(self):
        hashed = hash_password("super-secret")
        self.assertTrue(is_password_hash(hashed))
        self.assertTrue(verify_password("super-secret", hashed))
        self.assertFalse(verify_password("wrong", hashed))

    def test_verify_password_supports_legacy_plaintext(self):
        self.assertTrue(verify_password("legacy", "legacy"))
        self.assertFalse(verify_password("legacy", "different"))


if __name__ == "__main__":
    unittest.main()
