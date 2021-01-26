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
            communities={'64500:123'},
        ),
        roa_tree,
        communities_expected_invalid={'64500:42'},
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
            communities={'64500:123'},
        ),
        roa_tree,
        communities_expected_invalid=set(),
        verbose=True,
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
            "communities": {'64500:123'},
        },
        "roas": [
            {"prefix": "192.0.2.0/24", "asn": 64500, "max_length": 28},
            {"prefix": "192.0.2.0/24", "asn": 64501, "max_length": 24},
            {"prefix": "192.0.2.0/24", "asn": 0, "max_length": 24},
        ],
    } == result

    # This is invalid because max length, but the community
    result = validate(
        RouteEntry(
            origin=64501,
            aspath="64499 64501",
            prefix="192.0.2.0/28",
            prefix_length=28,
            peer_ip="192.0.2.0",
            peer_as=64511,
            communities={'64500:123'},
        ),
        roa_tree,
        communities_expected_invalid={'64500:123'},
        verbose=True,
    )
    assert RPKIStatus.invalid_expected == result["status"]

    # Under this origin AS, max length is 24
    result = validate(
        RouteEntry(
            origin=64501,
            aspath="64499 64501",
            prefix="192.0.2.0/28",
            prefix_length=28,
            peer_ip="192.0.2.0",
            peer_as=64511,
            communities={'64500:123'},
        ),
        roa_tree,
        communities_expected_invalid=set(),
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
            communities={'64500:123'},
        ),
        roa_tree,
        communities_expected_invalid=set(),
        verbose=True,
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
            communities=set(),
        ),
        roa_tree,
        communities_expected_invalid=set(),
        verbose=True,
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
            communities=set(),
        ),
        roa_tree,
        communities_expected_invalid=set(),
        verbose=True,
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
            communities=set(),
        ),
        roa_tree,
        communities_expected_invalid=set(),
        verbose=True,
    )
    assert RPKIStatus.invalid == result["status"]

    # Unknown origin should be not_found if there is no ROA
    result = validate(
        RouteEntry(
            origin=None,
            aspath="64499 {64500}",
            prefix="2001:db8::/32",
            prefix_length=32,
            peer_ip="192.0.2.0",
            peer_as=64511,
            communities=set(),
        ),
        roa_tree,
        communities_expected_invalid=set(),
        verbose=True,
    )
    assert RPKIStatus.not_found == result["status"]
