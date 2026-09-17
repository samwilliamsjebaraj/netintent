from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest
from pydantic import ValidationError

from netintent import Fabric, load_fabric
from netintent.cli import main

EXAMPLE = Path(__file__).parent.parent / "examples" / "clos-small.yaml"
Data = dict[str, Any]


def base() -> Data:
    return {
        "name": "t",
        "devices": [
            {"name": "s1", "role": "spine", "asn": 65000, "loopback": "10.0.0.1/32"},
            {"name": "l1", "role": "leaf", "asn": 65101, "loopback": "10.0.0.11/32"},
            {"name": "l2", "role": "leaf", "asn": 65102, "loopback": "10.0.0.12/32"},
        ],
        "links": [link("s1", "e1", "l1", "e1", "10.1.0.0/31")],
    }


def link(a: str, ai: str, b: str, bi: str, subnet: str) -> Data:
    return {
        "a": {"device": a, "interface": ai},
        "b": {"device": b, "interface": bi},
        "subnet": subnet,
    }


def test_example_is_valid() -> None:
    fabric = load_fabric(EXAMPLE)
    assert len(fabric.devices) == 4
    assert len(fabric.links) == 4


def test_spines_may_share_asn() -> None:
    data = base()
    data["devices"].append({"name": "s2", "role": "spine", "asn": 65000, "loopback": "10.0.0.2/32"})
    Fabric.model_validate(data)


def add_spine_to_spine_link(d: Data) -> None:
    d["devices"].append({"name": "s2", "role": "spine", "asn": 65000, "loopback": "10.0.0.2/32"})
    d["links"].append(link("s1", "e2", "s2", "e1", "10.1.0.2/31"))


CASES: list[tuple[Callable[[Data], None], str]] = [
    (lambda d: d["devices"][0].update(loopback="10.0.0.1/24"), "must be a /32"),
    (lambda d: d["devices"][1].update(loopback="10.0.0.1/32"), "used by s1 and l1"),
    (lambda d: d["devices"][0].update(asn=0), "greater than or equal to 1"),
    (lambda d: d["links"][0].update(subnet="10.1.0.0/30"), "must be a /31"),
    (lambda d: d["links"][0]["b"].update(device="ghost"), "unknown device ghost"),
    (lambda d: d["links"][0]["b"].update(device="s1"), "to itself"),
    (lambda d: d["devices"].append(dict(d["devices"][0])), "duplicate device name"),
    (
        lambda d: d["links"].append(link("s1", "e1", "l2", "e1", "10.1.0.2/31")),
        "used by more than one link",
    ),
    (lambda d: d["links"].append(link("s1", "e2", "l2", "e1", "10.1.0.0/31")), "overlaps"),
    (lambda d: d["links"].append(link("l1", "e2", "l2", "e2", "10.1.0.4/31")), "leaf-to-leaf"),
    (
        lambda d: d["links"].append(link("s1", "e3", "l2", "e3", "10.0.0.10/31")),
        "falls inside link subnet",
    ),
    (add_spine_to_spine_link, "spine-to-spine"),
    (lambda d: d["devices"][1].update(asn=65000), "eBGP peers need different ASNs"),
    (lambda d: d.update(unexpected=True), "Extra inputs are not permitted"),
]


@pytest.mark.parametrize(("mutate", "message"), CASES)
def test_invalid_intent_rejected(mutate: Callable[[Data], None], message: str) -> None:
    data = base()
    mutate(data)
    with pytest.raises(ValidationError, match=message):
        Fabric.model_validate(data)


def test_cli_ok(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["validate", str(EXAMPLE)]) == 0
    assert "OK: fabric 'lab-fabric'" in capsys.readouterr().out


def test_cli_invalid(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    bad = tmp_path / "bad.yaml"
    bad.write_text("name: x\ndevices: []\n")
    assert main(["validate", str(bad)]) == 1
    assert "INVALID" in capsys.readouterr().err


def test_cli_missing_file() -> None:
    assert main(["validate", "does-not-exist.yaml"]) == 2
