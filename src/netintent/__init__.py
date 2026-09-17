"""netintent: intent-driven network configuration and operations toolkit."""

from netintent.loader import load_fabric
from netintent.models import Device, Endpoint, Fabric, Link, Role

__all__ = ["Device", "Endpoint", "Fabric", "Link", "Role", "load_fabric"]
__version__ = "0.0.1"
