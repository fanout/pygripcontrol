import sys
import unittest

sys.path.append("../")
from src.response import Response


class TestResponse(unittest.TestCase):
    def test_initialize(self):
        response = Response()
        self.assertEqual(response.code, None)
        self.assertEqual(response.reason, None)
        self.assertEqual(response.headers, None)
        self.assertEqual(response.body, None)
        response = Response("code", "reason", "headers", "body")
        self.assertEqual(response.code, "code")
        self.assertEqual(response.reason, "reason")
        self.assertEqual(response.headers, "headers")
        self.assertEqual(response.body, "body")


if __name__ == "__main__":
    unittest.main()
