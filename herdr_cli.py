import json
import os
import subprocess

TOKEN = "description"
SOURCE = "erdinc.space-description"


class HerdrError(RuntimeError):
    pass


def run_herdr(*args):
    binary = os.environ.get("HERDR_BIN_PATH", "herdr")
    completed = subprocess.run([binary, *args], capture_output=True, text=True)
    if completed.returncode != 0:
        raise HerdrError(f"herdr {' '.join(args)} failed: {completed.stderr.strip()}")
    if not completed.stdout.strip():
        return None
    try:
        return json.loads(completed.stdout)["result"]
    except (json.JSONDecodeError, KeyError) as error:
        raise HerdrError(f"herdr {' '.join(args)} returned unexpected output: {completed.stdout!r}") from error


def set_description(workspace_id, description):
    run_herdr("workspace", "report-metadata", workspace_id, "--source", SOURCE,
              "--token", f"{TOKEN}={description}")


def clear_description(workspace_id):
    run_herdr("workspace", "report-metadata", workspace_id, "--source", SOURCE,
              "--clear-token", TOKEN)


def open_workspace_ids():
    return [workspace["workspace_id"] for workspace in run_herdr("workspace", "list")["workspaces"]]


def rename_workspace(workspace_id, name):
    run_herdr("workspace", "rename", workspace_id, name)


def workspace_label(workspace_id):
    return run_herdr("workspace", "get", workspace_id)["workspace"]["label"]
