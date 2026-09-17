import unittest
from service.health import health

class HealthTests(unittest.TestCase):
    def test_ok(self):
        self.assertEqual(health(), {"status": "ok"})
