import sys
import json
from struct import pack
import unittest

sys.path.append("../")
from src.gripcontrol import is_python3
from src.websocketevent import WebSocketEvent
from src.websocketcontext import WebSocketContext


def _b(s):
    if is_python3:
        assert isinstance(s, str)
        return s.encode("utf-8")
    else:
        assert not isinstance(s, unicode)
        return s


def _s(s):
    if is_python3:
        assert isinstance(s, str)
        return s
    else:
        assert not isinstance(s, unicode)
        return s.decode("utf-8")


class TestWebSocketContext(unittest.TestCase):
    def test_open(self):
        ws = WebSocketContext("conn-1", {}, [WebSocketEvent("OPEN")])
        self.assertEqual(ws.id, "conn-1")
        self.assertTrue(ws.is_opening())
        self.assertFalse(ws.can_recv())
        self.assertFalse(ws.accepted)
        ws.accept()
        self.assertTrue(ws.accepted)

    def test_recv(self):
        ws = WebSocketContext("conn-1", {}, [WebSocketEvent("TEXT", _b("hello"))])
        self.assertFalse(ws.is_opening())
        self.assertTrue(ws.can_recv())
        msg = ws.recv()
        self.assertEqual(msg, _s("hello"))
        self.assertFalse(ws.can_recv())

    def test_send(self):
        ws = WebSocketContext("conn-1", {}, [])
        self.assertFalse(ws.is_opening())
        self.assertFalse(ws.can_recv())
        self.assertEqual(len(ws.out_events), 0)
        ws.send(_b("apple"))
        ws.send(_s("banana"))
        ws.send_binary(_b("cherry"))
        ws.send_binary(_s("date"))
        self.assertEqual(len(ws.out_events), 4)
        self.assertEqual(ws.out_events[0].type, "TEXT")
        self.assertEqual(ws.out_events[0].content, _b("m:apple"))
        self.assertEqual(ws.out_events[1].type, "TEXT")
        self.assertEqual(ws.out_events[1].content, _b("m:banana"))
        self.assertEqual(ws.out_events[2].type, "BINARY")
        self.assertEqual(ws.out_events[2].content, _b("m:cherry"))
        self.assertEqual(ws.out_events[3].type, "BINARY")
        self.assertEqual(ws.out_events[3].content, _b("m:date"))

    def test_control(self):
        ws = WebSocketContext("conn-1", {}, [])
        self.assertEqual(len(ws.out_events), 0)
        ws.subscribe("foo")
        ws.unsubscribe("bar")
        self.assertEqual(len(ws.out_events), 2)

        self.assertEqual(ws.out_events[0].type, "TEXT")
        self.assertTrue(ws.out_events[0].content.startswith(_b("c:")))
        self.assertEqual(
            json.loads(ws.out_events[0].content[2:].decode("utf-8")),
            {_s("type"): _s("subscribe"), _s("channel"): _s("foo")},
        )

        self.assertEqual(ws.out_events[1].type, "TEXT")
        self.assertTrue(ws.out_events[1].content.startswith(_b("c:")))
        self.assertEqual(
            json.loads(ws.out_events[1].content[2:].decode("utf-8")),
            {_s("type"): _s("unsubscribe"), _s("channel"): _s("bar")},
        )

    def test_close(self):
        ws = WebSocketContext("conn-1", {}, [WebSocketEvent("CLOSE", pack(">H", 100))])
        self.assertFalse(ws.is_opening())
        self.assertTrue(ws.can_recv())
        msg = ws.recv()
        self.assertTrue(msg is None)
        self.assertEqual(ws.close_code, 100)

        ws = WebSocketContext("conn-1", {}, [])
        self.assertFalse(ws.is_opening())
        self.assertFalse(ws.can_recv())
        self.assertFalse(ws.closed)
        ws.close(code=100)
        self.assertEqual(ws.out_close_code, 100)

    def test_ping_pong(self):
        ws = WebSocketContext(
            "conn-1",
            {},
            [
                WebSocketEvent("PING", _b("ping1")),
                WebSocketEvent("PONG"),
                WebSocketEvent("TEXT", _b("hello")),
                WebSocketEvent("PING", _b("ping2")),
            ],
        )
        self.assertEqual(len(ws.out_events), 0)

        self.assertTrue(ws.can_recv())
        self.assertEqual(len(ws.out_events), 1)
        self.assertEqual(ws.out_events[0].type, "PONG")
        self.assertEqual(ws.out_events[0].content, _b("ping1"))

        self.assertTrue(ws.can_recv())
        self.assertEqual(len(ws.out_events), 1)

        msg = ws.recv()
        self.assertEqual(msg, "hello")
        self.assertEqual(len(ws.out_events), 1)

        self.assertFalse(ws.can_recv())
        self.assertEqual(len(ws.out_events), 2)
        self.assertEqual(ws.out_events[1].type, "PONG")
        self.assertEqual(ws.out_events[1].content, _b("ping2"))


if __name__ == "__main__":
    unittest.main()
