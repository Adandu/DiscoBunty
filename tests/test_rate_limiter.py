import unittest
import time
import sys
from unittest.mock import MagicMock

# Mock dependencies that are not available in the environment
sys.modules["config_manager"] = MagicMock()
sys.modules["models"] = MagicMock()
sys.modules["ssh_manager"] = MagicMock()
sys.modules["cryptography"] = MagicMock()
sys.modules["cryptography.fernet"] = MagicMock()

from app_state import LoginRateLimiter

class TestLoginRateLimiter(unittest.TestCase):
    def test_basic_limiting(self):
        limiter = LoginRateLimiter(max_attempts=3, window_seconds=10)
        self.assertTrue(limiter.is_allowed("user1"))
        self.assertTrue(limiter.is_allowed("user1"))
        self.assertTrue(limiter.is_allowed("user1"))
        # It should be blocked now
        self.assertFalse(limiter.is_allowed("user1"))

        # Other user should not be affected
        self.assertTrue(limiter.is_allowed("user2"))

    def test_window_expiration(self):
        # Using a very small window for testing expiration
        limiter = LoginRateLimiter(max_attempts=2, window_seconds=0.1)
        self.assertTrue(limiter.is_allowed("user1"))
        self.assertTrue(limiter.is_allowed("user1"))
        self.assertFalse(limiter.is_allowed("user1"))

        time.sleep(0.15)

        # After sleep, it should be allowed again
        self.assertTrue(limiter.is_allowed("user1"))

    def test_reset(self):
        limiter = LoginRateLimiter(max_attempts=2, window_seconds=60)
        self.assertTrue(limiter.is_allowed("user1"))
        self.assertTrue(limiter.is_allowed("user1"))
        self.assertFalse(limiter.is_allowed("user1"))

        limiter.reset("user1")
        self.assertTrue(limiter.is_allowed("user1"))

if __name__ == "__main__":
    unittest.main()
