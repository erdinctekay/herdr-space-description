import json
import os
import tomllib
from pathlib import Path

FILE_NAME = "descriptions.toml"
MAX_DESCRIPTION_LENGTH = 80  # herdr rejects longer token values


class StoreError(RuntimeError):
    pass


def descriptions_path():
    return Path(os.environ["HERDR_PLUGIN_CONFIG_DIR"]) / FILE_NAME


def validate(descriptions):
    for workspace_id, description in descriptions.items():
        if not isinstance(description, str):
            raise StoreError(f"{FILE_NAME}: {workspace_id} must be a string")
        if len(description) > MAX_DESCRIPTION_LENGTH:
            raise StoreError(f"{FILE_NAME}: {workspace_id} exceeds {MAX_DESCRIPTION_LENGTH} characters")


def load_descriptions():
    path = descriptions_path()
    try:
        with path.open("rb") as handle:
            descriptions = tomllib.load(handle)
    except FileNotFoundError as error:
        raise StoreError(f"{FILE_NAME} not found at {path}") from error
    except tomllib.TOMLDecodeError as error:
        raise StoreError(f"{FILE_NAME} is invalid: {error}") from error
    validate(descriptions)
    return descriptions


def toml_line(workspace_id, description):
    # JSON string escapes are a subset of TOML basic-string escapes.
    return f"{workspace_id} = {json.dumps(description, ensure_ascii=False)}\n"


def save_descriptions(descriptions):
    validate(descriptions)
    path = descriptions_path()
    staging = path.with_suffix(".tmp")
    staging.write_text("".join(toml_line(wid, descriptions[wid]) for wid in sorted(descriptions)),
                       encoding="utf-8")
    staging.replace(path)
