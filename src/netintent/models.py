"""Intent model for an eBGP Clos fabric.

v0.0.1 scope: describe devices and point-to-point links, and reject intent that
cannot be built. Configuration rendering comes in later releases.
"""

from __future__ import annotations

from enum import StrEnum
from ipaddress import IPv4Interface, IPv4Network
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

# 4-byte ASN range (RFC 6793). 0 and 4294967295 are reserved (RFC 7300).
ASN = Annotated[int, Field(ge=1, le=4294967294)]
Name = Annotated[str, Field(min_length=1, max_length=63, pattern=r"^[A-Za-z0-9][A-Za-z0-9._-]*$")]


class Role(StrEnum):
    SPINE = "spine"
    LEAF = "leaf"
    BORDER = "border"


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class Device(_Strict):
    name: Name
    role: Role
    asn: ASN
    loopback: IPv4Interface

    @field_validator("loopback")
    @classmethod
    def loopback_is_host_route(cls, v: IPv4Interface) -> IPv4Interface:
        if v.network.prefixlen != 32:
            raise ValueError(f"loopback {v} must be a /32")
        return v


class Endpoint(_Strict):
    device: Name
    interface: Annotated[str, Field(min_length=1)]


class Link(_Strict):
    a: Endpoint
    b: Endpoint
    subnet: IPv4Network

    @field_validator("subnet")
    @classmethod
    def subnet_is_p2p(cls, v: IPv4Network) -> IPv4Network:
        if v.prefixlen != 31:
            raise ValueError(f"link subnet {v} must be a /31 (RFC 3021)")
        return v

    @model_validator(mode="after")
    def not_a_loop(self) -> Link:
        if self.a.device == self.b.device:
            raise ValueError(f"link {self.subnet} connects {self.a.device} to itself")
        return self


class Fabric(_Strict):
    name: Name
    devices: list[Device] = Field(min_length=1)
    links: list[Link] = Field(default_factory=list)

    @model_validator(mode="after")
    def check_consistency(self) -> Fabric:
        errors: list[str] = []

        by_name: dict[str, Device] = {}
        for d in self.devices:
            if d.name in by_name:
                errors.append(f"duplicate device name: {d.name}")
            by_name[d.name] = d

        seen_lo: dict[IPv4Interface, str] = {}
        for d in self.devices:
            if d.loopback in seen_lo:
                errors.append(f"loopback {d.loopback} used by {seen_lo[d.loopback]} and {d.name}")
            seen_lo[d.loopback] = d.name

        used_ports: set[tuple[str, str]] = set()
        subnets: list[IPv4Network] = []
        for link in self.links:
            for ep in (link.a, link.b):
                if ep.device not in by_name:
                    errors.append(f"link {link.subnet} references unknown device {ep.device}")
                port = (ep.device, ep.interface)
                if port in used_ports:
                    errors.append(
                        f"interface {ep.device}:{ep.interface} used by more than one link"
                    )
                used_ports.add(port)

            for other in subnets:
                if link.subnet.overlaps(other):
                    errors.append(f"link subnet {link.subnet} overlaps {other}")
            subnets.append(link.subnet)

            for d in self.devices:
                if d.loopback.ip in link.subnet:
                    errors.append(f"loopback of {d.name} falls inside link subnet {link.subnet}")

            a, b = by_name.get(link.a.device), by_name.get(link.b.device)
            if a and b and a.role == b.role == Role.LEAF:
                errors.append(f"leaf-to-leaf link {a.name}-{b.name} is not valid in a Clos fabric")

        if errors:
            raise ValueError("; ".join(errors))
        return self
