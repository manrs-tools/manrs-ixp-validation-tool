import pytest
from aioresponses import aioresponses

from ..birdseye import get_routes
from ..status import RouteEntry

PAYLOAD_PROTOCOLS = {
    "protocols": {
        'peer1': {"state": "up", "neighbor_address": "192.0.2.1", "neighbor_as": 64501},
        'peer-ignored': {"state": "down", "neighbor_address": "192.0.2.2", "neighbor_as": 64502},
    },
}

PAYLOAD_ROUTES = {
    "routes": [
        {
            "network": "192.0.2.0/24",
            "bgp": {
                "as_path": [64501, 64502],
                "communities": [[64501, 1], [64501, 2]],
                "large_communities": [[64501, 10, 20]],
            },
        }
    ],
}


def prepare_get_routes(http_mock):
    http_mock.get(
        "http://example.net/api/protocols/bgp/",
        status=200,
        payload=PAYLOAD_PROTOCOLS,
    )
    http_mock.get(
        "http://example.net/api/routes/protocol/peer1",
        status=200,
        payload=PAYLOAD_ROUTES,
    )


@pytest.mark.asyncio
async def test_get_routes():
    with aioresponses() as http_mock:
        prepare_get_routes(http_mock)
        response = [r async for r in get_routes("http://example.net/api/")]
    print(response)
    assert response == [
        RouteEntry(
            origin=64502,
            aspath="64501 64502",
            prefix="192.0.2.0/24",
            peer_ip="192.0.2.1",
            peer_as=64501,
            communities={"64501:2", "64501:10:20", "64501:1"},
            source="Bird's Eye peer peer1",
        ),
    ]
