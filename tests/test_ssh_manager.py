import unittest
from ssh_manager import _humanize_age_seconds

class TestHumanizeAgeSeconds(unittest.TestCase):
    def test_empty_and_null_inputs(self):
        self.assertEqual(_humanize_age_seconds(None), "n/a")
        self.assertEqual(_humanize_age_seconds(""), "n/a")
        self.assertEqual(_humanize_age_seconds("   "), "n/a")
        self.assertEqual(_humanize_age_seconds("n/a"), "n/a")

    def test_invalid_values(self):
        self.assertEqual(_humanize_age_seconds("invalid"), "invalid")
        self.assertEqual(_humanize_age_seconds("not_a_number"), "not_a_number")

    def test_seconds_stripping_and_floats(self):
        self.assertEqual(_humanize_age_seconds("59s"), "59s")
        self.assertEqual(_humanize_age_seconds("59.5s"), "59s")
        self.assertEqual(_humanize_age_seconds("10"), "10s")

    def test_unit_conversions(self):
        self.assertEqual(_humanize_age_seconds("60"), "1m")
        self.assertEqual(_humanize_age_seconds("65"), "1m")
        self.assertEqual(_humanize_age_seconds("3600"), "1h")
        self.assertEqual(_humanize_age_seconds("3660"), "1h 1m")
        self.assertEqual(_humanize_age_seconds("86400"), "1d")
        self.assertEqual(_humanize_age_seconds("90000"), "1d 1h") # 86400 + 3600

    def test_two_part_limit(self):
        # 1 day + 1 hour + 1 minute (86400 + 3600 + 60 = 90060)
        self.assertEqual(_humanize_age_seconds("90060"), "1d 1h")

        # 1 hour + 1 minute + 1 second (3600 + 60 + 1 = 3661)
        self.assertEqual(_humanize_age_seconds("3661"), "1h 1m")

if __name__ == '__main__':
    unittest.main()
