import enum
from dataclasses import dataclass
from typing import Optional, Set


class RPKIStatus(enum.Enum):
    valid = "VALID"
    invalid = "INVALID"
    invalid_expected = "INVALID_EXPECTED"
    not_found = "NOT_FOUND"


@dataclass
class RouteEntry:
    origin: Optional[int]
    aspath: str
    prefix: str
    peer_ip: str
    peer_as: int
    communities: Set[str]
    source: Optional[str] = None
