from tests.support import PluginTestCase


class ApplyTest(PluginTestCase):
    def test_sets_description_token_for_each_listed_workspace(self):
        self.given_workspaces(w8="empty", wB="remote")
        self.given_file('w8 = "general"\nwB = "dailypedia-prod"\n')

        result = self.run_script("apply.py")

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.tokens("w8"), {"description": "general"})
        self.assertEqual(self.tokens("wB"), {"description": "dailypedia-prod"})

    def test_clears_description_of_workspaces_missing_from_file(self):
        self.given_workspaces(w8="empty", w5="cf-tunnel")
        self.given_tokens("w5", {"description": "stale", "other": "kept"})
        self.given_file('w8 = "general"\n')

        result = self.run_script("apply.py")

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.tokens("w5"), {"other": "kept"})
        self.assertEqual(self.tokens("w8"), {"description": "general"})

    def test_reports_unknown_ids_on_stderr_and_applies_the_rest(self):
        self.given_workspaces(w8="empty")
        self.given_file('w8 = "general"\nwZ = "gone"\n')

        result = self.run_script("apply.py")

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("wZ", result.stderr)
        self.assertEqual(self.tokens("w8"), {"description": "general"})

    def assert_fails_without_reports(self):
        result = self.run_script("apply.py")

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("descriptions.toml", result.stderr)
        self.assertNotIn("Traceback", result.stderr)
        self.assertEqual(self.metadata_calls(), [])

    def test_missing_file_fails_without_reports(self):
        self.given_workspaces(w8="empty")
        self.assert_fails_without_reports()

    def test_invalid_toml_fails_without_reports(self):
        self.given_workspaces(w8="empty")
        self.given_file('w8 = "general\n')
        self.assert_fails_without_reports()

    def test_non_string_value_fails_without_reports(self):
        self.given_workspaces(w8="empty", wB="remote")
        self.given_file('w8 = "general"\nwB = 3\n')
        self.assert_fails_without_reports()

    def test_value_over_token_limit_fails_without_reports(self):
        self.given_workspaces(w8="empty")
        self.given_file(f'w8 = "{"x" * 81}"\n')
        self.assert_fails_without_reports()

    def test_herdr_failure_exits_non_zero_with_message(self):
        self.given_workspaces(w8="empty")
        self.given_file('w8 = "general"\n')
        self.given_herdr_fails()

        result = self.run_script("apply.py")

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("fake herdr failure", result.stderr)
        self.assertNotIn("Traceback", result.stderr)
