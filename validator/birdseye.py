import asyncio
from typing import AsyncGenerator

import aiohttp
from aiohttp_retry import RetryClient

from validator.status import RouteEntry
from validator.utils import aio_get_json, route_tasks_to_route_entries


# noinspection PyTypeChecker
async def get_routes(base_url: str) -> AsyncGenerator[RouteEntry, None]:
    """
    Get the routes from a Bird's Eye LG instance, given a base URL.
    Returns a RouteEntry generator.
    """
    base_url = base_url.strip("/")
    connector = aiohttp.TCPConnector(limit=10)
    async with RetryClient(connector=connector, raise_for_status=False) as client:
        url = f"{base_url}/protocols/bgp/"
        protocols, _ = await aio_get_json(client, url, key="protocols")

        tasks = []
        for name, details in protocols.items():
            if details["state"] != "up":
                continue
            url = f"{base_url}/routes/protocol/{name}"
            peer_request_metadata = {
                "peer_ip": details["neighbor_address"],
                "peer_as": details["neighbor_as"],
                "peer_name": name,
            }
            task = aio_get_json(client, url, key="routes", metadata=peer_request_metadata)
            tasks.append(asyncio.ensure_future(task))

        async for entry in route_tasks_to_route_entries(tasks, "Bird's Eye"):
            yield entry
