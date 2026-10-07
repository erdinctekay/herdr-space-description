import json
import os
import pty
import select
import sys
import time

from tests.support import PLUGIN_ROOT, PluginTestCase

SCREEN_SETTLE_SECONDS = 0.3
EXIT_TIMEOUT_SECONDS = 10


class EditPopupTest(PluginTestCase):
    def run_popup(self, keystrokes):
        env = self.env(TERM="xterm", HERDR_PLUGIN_CONTEXT_JSON=json.dumps({"workspace_id": "w8"}))
        pid, fd = pty.fork()
        if pid == 0:
            os.execve(sys.executable, [sys.executable, str(PLUGIN_ROOT / "edit.py")], env)
        for chunk in keystrokes:
            self.drain(fd, SCREEN_SETTLE_SECONDS)
            os.write(fd, chunk.encode())
        deadline = time.monotonic() + EXIT_TIMEOUT_SECONDS
        while time.monotonic() < deadline:
            self.drain(fd, 0.1)
            finished, status = os.waitpid(pid, os.WNOHANG)
            if finished:
                os.close(fd)
                return os.waitstatus_to_exitcode(status)
        os.kill(pid, 9)
        self.fail("popup did not exit")

    @staticmethod
    def drain(fd, seconds):
        while select.select([fd], [], [], seconds)[0]:
            try:
                os.read(fd, 4096)
            except OSError:
                return

    def test_enter_saves_prefilled_and_edited_fields(self):
        self.given_workspaces(w8="empty")
        self.given_file('w8 = "general"\n')

        code = self.run_popup(["\x7f" * 5 + "scratch", "\t", "!", "\r"])

        self.assertEqual(code, 0)
        self.assertEqual(self.label("w8"), "scratch")
        self.assertEqual(self.tokens("w8"), {"description": "general!"})

    def test_ctrl_c_clears_active_field(self):
        self.given_workspaces(w8="empty")
        self.given_file('w8 = "general"\n')

        code = self.run_popup(["\t", "\x03", "\r"])

        self.assertEqual(code, 0)
        self.assertEqual(self.label("w8"), "empty")
        self.assertEqual(self.tokens("w8"), {})

    def test_escape_changes_nothing(self):
        self.given_workspaces(w8="empty")
        self.given_file('w8 = "general"\n')

        code = self.run_popup(["x", "\x1b"])

        self.assertEqual(code, 0)
        self.assertEqual(self.metadata_calls(), [])
        self.assertEqual(self.label("w8"), "empty")
