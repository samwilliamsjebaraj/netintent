# netintent

Intent-driven network configuration and operations toolkit.

> **Status: pre-alpha (v0.0.1).** The API will change. Not for production use yet.

## What it does today

`netintent` validates the intent for an eBGP Clos fabric before anything reaches a device. It rejects intent that cannot be built:

- Loopbacks that are not /32, or are duplicated
- Link subnets that are not /31 (RFC 3021), or that overlap
- Links to unknown devices, self-loops, and interfaces used by more than one link
- Loopbacks that fall inside a link subnet
- Leaf-to-leaf links in a Clos fabric
- Invalid or reserved ASNs, and unknown fields

Spines may share an ASN, as in the RFC 7938 design.

## Install

```bash
pip install netintent
```

## Usage

```bash
netintent validate examples/clos-small.yaml
# OK: fabric 'lab-fabric' - 4 devices, 4 links
```

```python
from netintent import load_fabric

fabric = load_fabric("examples/clos-small.yaml")
print([d.name for d in fabric.devices])
```

## Roadmap

- Configuration rendering for multiple vendors from validated intent
- Source-of-truth integration
- Operational state checks against intent
- An evaluated AI triage layer for fabric faults, with a public benchmark

## Development

```bash
uv sync
uv run pytest
uv run ruff check . && uv run mypy src
```

This project is developed with AI assistance. All code is specified, reviewed, and tested by the maintainer.

## License

Apache-2.0
