import sys
import unittest

sys.path.append("../")
from src.channel import Channel


class TestChannel(unittest.TestCase):
    def test_initialize(self):
        channel = Channel("name")
        self.assertEqual(channel.name, "name")
        self.assertEqual(channel.prev_id, None)

        channel = Channel("name", "prev-id")
        self.assertEqual(channel.name, "name")
        self.assertEqual(channel.prev_id, "prev-id")


if __name__ == "__main__":
    unittest.main()
