import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parent.parent
FAKE_HERDR = Path(__file__).resolve().parent / "fake_herdr.py"


class PluginTestCase(unittest.TestCase):
    """Runs plugin scripts against the fake herdr with a throwaway config dir."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.config_dir = self.tmp / "config"
        self.config_dir.mkdir()
        self.state_path = self.tmp / "state.json"
        self.log_path = self.tmp / "calls.log"
        self.log_path.touch()

    def given_workspaces(self, **labels):
        workspaces = {wid: {"label": label, "tokens": {}} for wid, label in labels.items()}
        self.state_path.write_text(json.dumps({"workspaces": workspaces}))

    def given_tokens(self, workspace_id, tokens):
        state = json.loads(self.state_path.read_text())
        state["workspaces"][workspace_id]["tokens"] = tokens
        self.state_path.write_text(json.dumps(state))

    def given_herdr_fails(self):
        state = json.loads(self.state_path.read_text())
        state["fail"] = True
        self.state_path.write_text(json.dumps(state))

    def given_file(self, text):
        self.descriptions_path.write_text(text, encoding="utf-8")

    @property
    def descriptions_path(self):
        return self.config_dir / "descriptions.toml"

    def env(self, **extra):
        return {
            **os.environ,
            "HERDR_BIN_PATH": str(FAKE_HERDR),
            "HERDR_PLUGIN_CONFIG_DIR": str(self.config_dir),
            "FAKE_HERDR_STATE": str(self.state_path),
            "FAKE_HERDR_LOG": str(self.log_path),
            **extra,
        }

    def run_script(self, script, *args, **extra_env):
        return subprocess.run(
            [sys.executable, str(PLUGIN_ROOT / script), *args],
            env=self.env(**extra_env),
            capture_output=True,
            text=True,
            timeout=30,
        )

    def tokens(self, workspace_id):
        state = json.loads(self.state_path.read_text())
        return state["workspaces"][workspace_id]["tokens"]

    def label(self, workspace_id):
        return json.loads(self.state_path.read_text())["workspaces"][workspace_id]["label"]

    def herdr_calls(self):
        return [json.loads(line) for line in self.log_path.read_text().splitlines()]

    def metadata_calls(self):
        return [call for call in self.herdr_calls() if call[:2] == ["workspace", "report-metadata"]]
