import asyncio
from typing import Any, Optional, List, Union, Dict

import aiohttp

from validator.status import RouteEntry


async def aio_get_json(
    client: aiohttp.ClientSession,
    url: str,
    key: Optional[List[str]] = None,
    metadata: Any = None,
    ssl_verify: bool = True,
):
    """
    Do an async HTTP request for JSON data, with the given client and url.
    If key is given, that key from the JSON is returned. Return value
    is a tuple of JSON data and the metadata parameter.
    """
    async with client.get(url, ssl=None if ssl_verify else False) as resp:
        json = await resp.json()

        return get_data_from_json(json, key), metadata


def get_data_from_json(json: Dict[str, Any], key: Optional[List[str]] = None):
    if key is None:
        return json
    for this_key in key:
        if json.get(this_key) is not None:
            return json[this_key]
    return None


async def route_tasks_to_route_entries(tasks, source_name: str):
    """
    Given a set of futures, which request route entries from an Alice or Bird's Eye LG,
    execute the features, parse their output, and yield RouteEntry instances.

    Alice and Bird's Eye route query outputs are almost identical, allowing this
    same code to be used for handling either.
    """
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
