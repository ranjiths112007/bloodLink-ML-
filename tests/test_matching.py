import unittest

from blood_rules import is_compatible, is_eligible_by_age, is_eligible_by_recency


class SafetyRuleTests(unittest.TestCase):
    def test_blood_compatibility(self):
        self.assertTrue(is_compatible("O-", "AB+"))
        self.assertTrue(is_compatible("O+", "O+"))
        self.assertFalse(is_compatible("AB+", "O+"))

    def test_recency(self):
        self.assertTrue(is_eligible_by_recency(None))
        self.assertFalse(is_eligible_by_recency(89))
        self.assertTrue(is_eligible_by_recency(90))

    def test_age(self):
        self.assertFalse(is_eligible_by_age(17))
        self.assertTrue(is_eligible_by_age(18))
        self.assertTrue(is_eligible_by_age(65))
        self.assertFalse(is_eligible_by_age(66))


if __name__ == "__main__":
    unittest.main()
