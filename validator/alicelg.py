import asyncio
from typing import AsyncGenerator, Dict, List, Optional

import aiohttp
from aiohttp_retry import RetryClient

from validator.status import RouteEntry
from validator.utils import aio_get_json, route_tasks_to_route_entries


async def query_rpki_invalid_community(base_url: str) -> Optional[str]:
    """
    Retrieve the RPKI invalid community from an Alice LG instance.
    Returns None if not found.
    """
    async with RetryClient(raise_for_status=False) as client:
        json, _ = await aio_get_json(client, base_url + "/config")
        invalid = json.get("rpki", {}).get("invalid")
        if invalid:
            return ":".join(invalid)
        return None


# noinspection PyTypeChecker
async def get_routes(
    base_url: str, group: Optional[str] = None
) -> AsyncGenerator[RouteEntry, None]:
    """
    Get the routes from an Alice LG instance, given a base URL.
    Optionally filters for a particular group. Returns a RouteEntry
    generator.
    """
    connector = aiohttp.TCPConnector(limit=10)
    async with RetryClient(connector=connector, raise_for_status=False) as client:
        route_servers, _ = await aio_get_json(
            client, base_url + "/routeservers", key="routeservers"
        )
        if group:
            route_servers = [r for r in route_servers if r["group"] == group]

        rs_neighbors = await _query_rs_neighbors(base_url, client, route_servers)

        tasks = []
        for peers, metadata in rs_neighbors:
            for peer in peers:
                if peer["state"] != "up":
                    continue
                url = f'{base_url}/routeservers/{metadata["route_server"]}/neighbors/{peer["id"]}/routes'
                peer_request_metadata = {
                    "peer_ip": peer["address"],
                    "peer_as": peer["asn"],
                    "peer_name": peer["id"],
                    "route_server": metadata["route_server"],
                }
                task = aio_get_json(client, url, key="imported", metadata=peer_request_metadata)
                tasks.append(asyncio.ensure_future(task))

        async for entry in route_tasks_to_route_entries(tasks, "Alice LG"):
            yield entry


async def _query_rs_neighbors(
    base_url: str, client: aiohttp.ClientSession, route_servers: List[Dict[str, str]]
):
    """
    Query the neighbors of a list of route servers, as returned by Alice LG.
    """
    tasks = []
    for route_server in route_servers:
        url = f'{base_url}/routeservers/{route_server["id"]}/neighbors'
        task = aio_get_json(
            client, url, key="neighbours", metadata={"route_server": route_server["id"]}
        )
        tasks.append(asyncio.ensure_future(task))
    return await asyncio.gather(*tasks)
