import sys
import unittest

sys.path.append("../")
from src.websocketevent import WebSocketEvent


class TestWebSocketEvent(unittest.TestCase):
    def test_initialize(self):
        event = WebSocketEvent("type")
        self.assertEqual(event.type, "type")
        self.assertEqual(event.content, None)
        event = WebSocketEvent("type", "content")
        self.assertEqual(event.type, "type")
        self.assertEqual(event.content, "content")


if __name__ == "__main__":
    unittest.main()
