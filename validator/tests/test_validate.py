import radix

from ..status import RouteEntry, RPKIStatus
from ..validate import validate


def test_validate():
    roa_tree = radix.Radix()
    rnode = roa_tree.add("192.0.2.0/24")
    rnode.data["roas"] = [
        {"asn": 64500, "max_length": 28},
        {"asn": 64501, "max_length": 24},
        {"asn": 0, "max_length": 24},
    ]

    # Valid route, does not return anything
    result = validate(
        RouteEntry(
            origin=64500,
            aspath="64499 64500",
            prefix="192.0.2.0/28",
            prefix_length=28,
            peer_ip="192.0.2.0",
            peer_as=64511,
        ),
        roa_tree,
    )
    assert not result

    # Valid route with full info returned
    result = validate(
        RouteEntry(
            origin=64500,
            aspath="64499 64500",
            prefix="192.0.2.0/28",
            prefix_length=28,
            peer_ip="192.0.2.0",
            peer_as=64511,
        ),
        roa_tree,
        return_all=True,
    )
    assert {
        "status": RPKIStatus.valid,
        "route": {
            "origin": 64500,
            "aspath": "64499 64500",
            "prefix": "192.0.2.0/28",
            "prefix_length": 28,
            "peer_ip": "192.0.2.0",
            "peer_as": 64511,
        },
        "roas": [
            {"prefix": "192.0.2.0/24", "asn": 64500, "max_length": 28},
            {"prefix": "192.0.2.0/24", "asn": 64501, "max_length": 24},
            {"prefix": "192.0.2.0/24", "asn": 0, "max_length": 24},
        ],
    } == result

    # Under this origin AS, max length is 24
    result = validate(
        RouteEntry(
            origin=64501,
            aspath="64499 64501",
            prefix="192.0.2.0/28",
            prefix_length=28,
            peer_ip="192.0.2.0",
            peer_as=64511,
        ),
        roa_tree,
    )
    assert RPKIStatus.invalid == result["status"]

    # Retry with a valid length for this origin AS
    result = validate(
        RouteEntry(
            origin=64501,
            aspath="64499 64501",
            prefix="192.0.2.0/24",
            prefix_length=24,
            peer_ip="192.0.2.0",
            peer_as=64511,
        ),
        roa_tree,
        return_all=True,
    )
    assert RPKIStatus.valid == result["status"]

    # No ROA
    result = validate(
        RouteEntry(
            origin=64501,
            aspath="64499 64501",
            prefix="2001:db8::/32",
            prefix_length=32,
            peer_ip="192.0.2.0",
            peer_as=64511,
        ),
        roa_tree,
        return_all=True,
    )
    assert RPKIStatus.not_found == result["status"]

    # Origin unknown should never validate if there is a ROA
    result = validate(
        RouteEntry(
            origin=None,
            aspath="64499 {64500}",
            prefix="192.0.2.0/24",
            prefix_length=24,
            peer_ip="192.0.2.0",
            peer_as=64511,
        ),
        roa_tree,
        return_all=True,
    )
    assert RPKIStatus.invalid == result["status"]

    # Origin AS0 should never validate if there is a ROA
    result = validate(
        RouteEntry(
            origin=0,
            aspath="64499 0",
            prefix="192.0.2.0/24",
            prefix_length=24,
            peer_ip="192.0.2.0",
            peer_as=64511,
        ),
        roa_tree,
        return_all=True,
    )
    assert RPKIStatus.invalid == result["status"]

    # Unknown should be not_found if there is no ROA
    result = validate(
        RouteEntry(
            origin=None,
            aspath="64499 {64500}",
            prefix="2001:db8::/32",
            prefix_length=32,
            peer_ip="192.0.2.0",
            peer_as=64511,
        ),
        roa_tree,
        return_all=True,
    )
    assert RPKIStatus.not_found == result["status"]
