import unittest
from service.config import HOST, PORT

class ConfigTests(unittest.TestCase):
    def test_local_binding(self):
        self.assertEqual(HOST, "127.0.0.1")
        self.assertEqual(PORT, 8000)
