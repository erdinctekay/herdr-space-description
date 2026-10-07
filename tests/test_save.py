import tomllib
from unittest import mock

from tests.support import PluginTestCase


class SaveTest(PluginTestCase):
    def save(self, workspace_id, name, description):
        from edit import save
        with mock.patch.dict("os.environ", self.env(), clear=True):
            save(workspace_id, name, description)

    def saved_file(self):
        return tomllib.loads(self.descriptions_path.read_text(encoding="utf-8"))

    def test_renames_writes_and_applies(self):
        self.given_workspaces(w8="empty", wB="remote")
        self.given_file('wB = "dailypedia-prod"\n')

        self.save("w8", "scratch", "general")

        self.assertEqual(self.label("w8"), "scratch")
        self.assertEqual(self.saved_file(), {"w8": "general", "wB": "dailypedia-prod"})
        self.assertEqual(self.tokens("w8"), {"description": "general"})
        self.assertEqual(self.tokens("wB"), {"description": "dailypedia-prod"})

    def test_empty_description_removes_entry_and_clears_token(self):
        self.given_workspaces(w8="empty")
        self.given_tokens("w8", {"description": "general"})
        self.given_file('w8 = "general"\n')

        self.save("w8", "empty", "  ")

        self.assertEqual(self.saved_file(), {})
        self.assertEqual(self.tokens("w8"), {})

    def test_empty_name_keeps_current_name(self):
        self.given_workspaces(w8="empty")
        self.given_file("")

        self.save("w8", " ", "general")

        self.assertEqual(self.label("w8"), "empty")
        self.assertNotIn("rename", [call[1] for call in self.herdr_calls()])

    def test_creates_file_when_missing(self):
        self.given_workspaces(w8="empty")

        self.save("w8", "empty", "general")

        self.assertEqual(self.saved_file(), {"w8": "general"})

    def test_quotes_and_unicode_round_trip(self):
        self.given_workspaces(w8="empty")
        self.given_file("")
        description = 'say "hi" \\ çğü\ttab'

        self.save("w8", "empty", description)

        self.assertEqual(self.saved_file(), {"w8": description})

    def test_too_long_description_changes_nothing(self):
        from store import StoreError
        self.given_workspaces(w8="empty")
        self.given_file('w8 = "general"\n')

        with self.assertRaises(StoreError):
            self.save("w8", "renamed", "x" * 81)

        self.assertEqual(self.label("w8"), "empty")
        self.assertEqual(self.saved_file(), {"w8": "general"})
