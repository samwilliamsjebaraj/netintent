"""Load fabric intent from YAML."""

from __future__ import annotations

from pathlib import Path

import yaml

from netintent.models import Fabric


def load_fabric(path: str | Path) -> Fabric:
    """Parse and validate a fabric intent file.

    Raises pydantic.ValidationError if the intent is invalid.
    """
    with Path(path).open(encoding="utf-8") as fh:
        data = yaml.safe_load(fh)
    return Fabric.model_validate(data)
