from pathlib import Path

from ..mrt import RouteEntry, parse_mrt


def test_parse_mrt():
    # This is an MRT file containing all routes under 185.186.0.0/16
    # as seen from an NL-IX route server session with RPKI checks disabled
    mrt_file = Path(__file__).parent / "185.186.nlix.mrt"
    with open(mrt_file, "rb") as f:
        entries = list(parse_mrt(f))

    assert 23 == len(entries)
    assert (
        RouteEntry(
            origin=206350,
            aspath="8529 28885 206350",
            prefix="185.186.205.0/24",
            prefix_length=24,
            peer_ip="193.239.116.255",
            peer_as=34307,
        )
        == entries[0]
    )
    # Originated from an AS-SET, so non origin
    assert (
        RouteEntry(
            origin=None,
            aspath="8529 28885 {206350}",
            prefix="185.186.206.0/24",
            prefix_length=24,
            peer_ip="193.239.116.255",
            peer_as=34307,
        )
        == entries[1]
    )
