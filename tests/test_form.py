import curses
import unittest

from form import Field


def typed(field, *keys):
    for key in keys:
        field.handle(key)
    return field


class FieldTest(unittest.TestCase):
    def test_inserts_at_cursor_and_deletes_backwards(self):
        field = typed(Field("Name", "ac"), curses.KEY_LEFT, "b", curses.KEY_END, "\x7f")
        self.assertEqual(field.text, "ab")

    def test_stops_at_max_length(self):
        field = typed(Field("Description", "abc", max_length=4), "d", "e")
        self.assertEqual(field.text, "abcd")

    def test_ignores_control_characters(self):
        field = typed(Field("Name", "a"), "\x01", curses.KEY_RESIZE)
        self.assertEqual(field.text, "a")
