import enum
from dataclasses import dataclass
from typing import Optional


@dataclass
class RouteEntry:
    origin: Optional[int]
    aspath: str
    prefix: str
    prefix_length: int
    peer_ip: str
    peer_as: int


class RPKIStatus(enum.Enum):
    valid = "VALID"
    invalid = "INVALID"
    not_found = "NOT_FOUND"
