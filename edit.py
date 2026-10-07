import curses
import json
import os
import sys

from apply import apply_descriptions
from form import Field, run_form
from herdr_cli import HerdrError, rename_workspace, workspace_label
from store import MAX_DESCRIPTION_LENGTH, StoreError, descriptions_path, load_descriptions, save_descriptions

ESC_DELAY_MS = "25"
DIRECT_COLOR_TERM = "xterm-direct"
TRUECOLOR_VALUES = {"truecolor", "24bit"}


def current_descriptions():
    return load_descriptions() if descriptions_path().exists() else {}


def save(workspace_id, name, description):
    descriptions = current_descriptions()
    description = description.strip()
    if description:
        descriptions[workspace_id] = description
    else:
        descriptions.pop(workspace_id, None)
    save_descriptions(descriptions)
    name = name.strip()
    if name:
        rename_workspace(workspace_id, name)
    apply_descriptions()


def focused_workspace_id():
    return json.loads(os.environ["HERDR_PLUGIN_CONTEXT_JSON"])["workspace_id"]


def submit_handler(workspace_id):
    def submit(name, description):
        try:
            save(workspace_id, name, description)
        except (StoreError, HerdrError) as error:
            return f"Error: {error}"
        return None
    return submit


def prefer_direct_color():
    if os.environ.get("COLORTERM") not in TRUECOLOR_VALUES:
        return
    try:
        curses.setupterm(DIRECT_COLOR_TERM)
    except curses.error:
        return  # no terminfo entry: keep TERM and its 256-color palette
    os.environ["TERM"] = DIRECT_COLOR_TERM


def main():
    try:
        workspace_id = focused_workspace_id()
        fields = [
            Field("name", workspace_label(workspace_id)),
            Field("description", current_descriptions().get(workspace_id, ""), MAX_DESCRIPTION_LENGTH),
        ]
    except (KeyError, json.JSONDecodeError, StoreError, HerdrError) as error:
        print(f"space-description: {error}", file=sys.stderr)
        return 1
    os.environ.setdefault("ESCDELAY", ESC_DELAY_MS)
    prefer_direct_color()
    curses.wrapper(run_form, fields, submit_handler(workspace_id))
    return 0


if __name__ == "__main__":
    sys.exit(main())
