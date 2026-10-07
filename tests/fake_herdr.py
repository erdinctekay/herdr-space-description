#!/usr/bin/env python3
"""Stand-in for the herdr CLI: serves workspaces from a JSON state file and logs every call."""
import json
import os
import sys

STATE_PATH = os.environ["FAKE_HERDR_STATE"]
LOG_PATH = os.environ["FAKE_HERDR_LOG"]


def load_state():
    with open(STATE_PATH, encoding="utf-8") as handle:
        return json.load(handle)


def save_state(state):
    with open(STATE_PATH, "w", encoding="utf-8") as handle:
        json.dump(state, handle)


def option_values(args, name):
    return [args[i + 1] for i, arg in enumerate(args[:-1]) if arg == name]


def report_metadata(state, args):
    workspace_id = args[0]
    tokens = state["workspaces"][workspace_id].setdefault("tokens", {})
    for pair in option_values(args, "--token"):
        name, value = pair.split("=", 1)
        tokens[name] = value
    for name in option_values(args, "--clear-token"):
        tokens.pop(name, None)
    save_state(state)
    return None


def main(args):
    with open(LOG_PATH, "a", encoding="utf-8") as log:
        log.write(json.dumps(args) + "\n")
    state = load_state()
    if state.get("fail"):
        print("fake herdr failure", file=sys.stderr)
        return 1
    command = args[:2]
    if any(arg.startswith("--") for arg in args[2:3]):
        # Real herdr only accepts options after the positional workspace id.
        print(f"unknown option: {args[3] if len(args) > 3 else args[2]}", file=sys.stderr)
        return 2
    if command == ["workspace", "list"]:
        workspaces = [{"workspace_id": wid, "label": ws["label"]} for wid, ws in state["workspaces"].items()]
        result = {"type": "workspace_list", "workspaces": workspaces}
    elif command == ["workspace", "get"]:
        workspace = dict(state["workspaces"][args[2]], workspace_id=args[2])
        result = {"type": "workspace_info", "workspace": workspace}
    elif command == ["workspace", "rename"]:
        state["workspaces"][args[2]]["label"] = " ".join(args[3:])
        save_state(state)
        result = {"type": "ok"}
    elif command == ["workspace", "report-metadata"]:
        result = report_metadata(state, args[2:])
    else:
        print(f"fake herdr: unsupported {args}", file=sys.stderr)
        return 2
    if result is not None:
        print(json.dumps({"id": "cli", "result": result}))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
