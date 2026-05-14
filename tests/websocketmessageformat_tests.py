import sys
import unittest
from base64 import b64encode

sys.path.append("../")
from src.websocketmessageformat import WebSocketMessageFormat


class TestWebSocketMessageFormat(unittest.TestCase):
    def test_initialize(self):
        format = WebSocketMessageFormat("content")
        self.assertEqual(format.content, "content")
        self.assertEqual(format.binary, False)
        format = WebSocketMessageFormat("content", True)
        self.assertEqual(format.content, "content")
        self.assertEqual(format.binary, True)

    def test_name(self):
        format = WebSocketMessageFormat("content")
        self.assertEqual(format.name(), "ws-message")

    def test_export(self):
        format = WebSocketMessageFormat("content")
        self.assertEqual(format.export(), {"content": "content"})
        format = WebSocketMessageFormat("content", True)
        self.assertEqual(
            format.export(), {"content-bin": b64encode("content".encode("ascii"))}
        )

    def test_action(self):
        format = WebSocketMessageFormat(action="close")
        self.assertEqual(format.export(), {"action": "close"})
        format = WebSocketMessageFormat(action="close", code=1013, reason="bye for now")
        self.assertEqual(
            format.export(), {"action": "close", "code": 1013, "reason": "bye for now"}
        )


if __name__ == "__main__":
    unittest.main()
