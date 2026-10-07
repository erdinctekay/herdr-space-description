import sys

from herdr_cli import HerdrError, clear_description, open_workspace_ids, set_description
from store import StoreError, load_descriptions


def apply_descriptions():
    descriptions = load_descriptions()
    open_ids = open_workspace_ids()
    for workspace_id in sorted(set(descriptions) - set(open_ids)):
        print(f"space-description: no open workspace {workspace_id}; skipped", file=sys.stderr)
    for workspace_id in open_ids:
        if workspace_id in descriptions:
            set_description(workspace_id, descriptions[workspace_id])
        else:
            clear_description(workspace_id)


def main():
    try:
        apply_descriptions()
    except (StoreError, HerdrError) as error:
        print(f"space-description: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
