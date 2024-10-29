import asyncio
from typing import AsyncGenerator, Dict, List, Optional, Set

import aiohttp
from aiohttp_retry import ExponentialRetry, RetryClient

from validator.status import RouteEntry
from validator.utils import aio_get_json, route_tasks_to_route_entries


async def query_rpki_invalid_community(base_url: str, ssl_verify: bool) -> Set[str]:
    """
    Retrieve the RPKI invalid communities from an Alice LG instance.
    Older only have one community, newer instances may have multiple.
    Returns empty set if not found.
    """
    async with RetryClient(raise_for_status=False) as client:
        json, _ = await aio_get_json(client, base_url + "/config", ssl_verify=ssl_verify)
        invalid = json.get("rpki", {}).get("invalid")
        if invalid:
            if isinstance(invalid[0], list):
                return {":".join(invalid_item) for invalid_item in invalid}
            else:
                return {":".join(invalid)}
        return set()


# noinspection PyTypeChecker
async def get_routes(
    base_url: str, group: Optional[str] = None, ssl_verify: bool = True
) -> AsyncGenerator[RouteEntry, None]:
    """
    Get the routes from an Alice LG instance, given a base URL.
    Optionally filters for a particular group. Returns a RouteEntry
    generator.
    """
    connector = aiohttp.TCPConnector(limit=5)
    options = ExponentialRetry(
        attempts=5, start_timeout=2, exceptions=[aiohttp.client_exceptions.ContentTypeError]
    )
    timeout = aiohttp.ClientTimeout(total=60000)
    async with RetryClient(
        retry_options=options, connector=connector, raise_for_status=False, timeout=timeout
    ) as client:
        route_servers, _ = await aio_get_json(
            client, base_url + "/routeservers", key=["routeservers"], ssl_verify=ssl_verify
        )
        if group:
            route_servers = [r for r in route_servers if r["group"] == group]

        rs_neighbors = await _query_rs_neighbors(base_url, client, route_servers, ssl_verify)

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
                task = aio_get_json(
                    client,
                    url,
                    key=["imported"],
                    metadata=peer_request_metadata,
                    ssl_verify=ssl_verify,
                )
                tasks.append(asyncio.ensure_future(task))

        async for entry in route_tasks_to_route_entries(tasks, "Alice LG"):
            yield entry


async def _query_rs_neighbors(
    base_url: str,
    client: aiohttp.ClientSession,
    route_servers: List[Dict[str, str]],
    ssl_verify: bool,
):
    """
    Query the neighbors of a list of route servers, as returned by Alice LG.
    """
    tasks = []
    for route_server in route_servers:
        url = f'{base_url}/routeservers/{route_server["id"]}/neighbors'
        task = aio_get_json(
            client,
            url,
            key=["neighbors", "neighbours"],
            metadata={"route_server": route_server["id"]},
            ssl_verify=ssl_verify,
        )
        tasks.append(asyncio.ensure_future(task))
    return await asyncio.gather(*tasks)
