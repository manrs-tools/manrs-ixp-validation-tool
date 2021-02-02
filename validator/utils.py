import asyncio
from typing import Any, Optional

import aiohttp

from validator.status import RouteEntry


async def aio_get_json(
    client: aiohttp.ClientSession, url: str, key: Optional[str] = None, metadata: Any = None
):
    """
    Do an async HTTP request for JSON data, with the given client and url.
    If key is given, that key from the JSON is returned. Return value
    is a tuple of JSON data and the metadata parameter.
    """
    async with client.get(url) as resp:
        json = await resp.json()
        if key:
            return json[key], metadata
        return json, metadata


async def route_tasks_to_route_entry(tasks, source_name: str):
    for result in asyncio.as_completed(tasks):
        imported_routes, metadata = await result
        for imported_route in imported_routes:
            communities = imported_route["bgp"].get("communities", []) + imported_route["bgp"].get(
                "large_communities", []
            )
            communities_set = {
                ":".join([str(segment) for segment in community]) for community in communities
            }
            source = source_name.strip()
            if "route_server" in metadata:
                source += " route server " + metadata["route_server"]
            if "peer_name" in metadata:
                source += " peer " + metadata["peer_name"]
            route_entry = RouteEntry(
                origin=int(imported_route["bgp"]["as_path"][-1]),
                aspath=" ".join([str(asn) for asn in imported_route["bgp"]["as_path"]]),
                prefix=imported_route["network"],
                peer_ip=metadata["peer_ip"],
                peer_as=metadata["peer_as"],
                communities=communities_set,
                source=source,
            )
            yield route_entry
