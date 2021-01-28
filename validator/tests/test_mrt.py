from pathlib import Path
import pytest

from ..mrt import RouteEntry, parse_mrt


@pytest.mark.asyncio
async def test_parse_mrt_v2():
    # This is an MRT file containing all routes under 185.186.0.0/16
    # as seen from an NL-IX route server session with RPKI checks disabled
    mrt_file = Path(__file__).parent / "185.186.nlix.mrt"
    entries = [entry async for entry in parse_mrt(mrt_file)]

    assert 23 == len(entries)
    assert (
        RouteEntry(
            origin=206350,
            aspath="8529 28885 206350",
            prefix="185.186.205.0/24",
            peer_ip="193.239.116.255",
            peer_as=34307,
            communities={
                "213279:34307:492",
                "8529:707",
                "8529:30",
                "213279:8529:492",
                "34307:52210",
            },
        )
        == entries[0]
    )
    # Originated from an AS-SET, so non origin
    assert (
        RouteEntry(
            origin=None,
            aspath="8529 28885 {206350}",
            prefix="185.186.206.0/24",
            peer_ip="193.239.116.255",
            peer_as=34307,
            communities={
                "34307:52210",
                "213279:34307:492",
                "213279:1101:9",
                "8529:30",
                "8529:707",
                "34307:60004",
                "213279:1103:492",
                "213279:8529:492",
            },
        )
        == entries[1]
    )


@pytest.mark.asyncio
async def test_parse_mrt_v1():
    # This is an MRT file containing a NAMEX snapshot in table dump v1
    # format, including cases where the AS path attribute contains 23456
    mrt_file = Path(__file__).parent / "namex-bgpd-rib-inet6.mrt"
    entries = [entry async for entry in parse_mrt(mrt_file)]

    assert 432 == len(entries)
    # Record 9 contains AS23456 in AS path, but has an AS4 path
    assert (
        RouteEntry(
            origin=197440,
            aspath="197440",
            prefix="2001:678:12::/48",
            peer_ip="2001:7f8:10::19:7440",
            peer_as=23456,
            communities=set(),
        )
        == entries[9]
    )
