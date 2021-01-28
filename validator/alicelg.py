import asyncio
from typing import Any, AsyncGenerator, Dict, List, Optional

import aiohttp
from aiohttp_retry import RetryClient

from validator.status import RouteEntry


async def aio_get_json(
    client: aiohttp.ClientSession, url: str, key: Optional[str] = None, metadata: Any = None
):
    # print(f'req {url}')
    async with client.get(url) as resp:
        json = await resp.json()
        # print(f'done {url}')
        if key:
            return json[key], metadata
        return json, metadata


async def query_rpki_invalid_community(base_url: str) -> Optional[str]:
    async with RetryClient(raise_for_status=False) as client:
        json, _ = await aio_get_json(client, base_url + '/config')
        invalid = json.get('rpki', {}).get('invalid')
        if invalid:
            return ':'.join(invalid)
        return None


# noinspection PyTypeChecker
async def get_routes(
    base_url: str, group: Optional[str] = None
) -> AsyncGenerator[RouteEntry, None]:
    connector = aiohttp.TCPConnector(limit=10)
    async with RetryClient(connector=connector, raise_for_status=False) as client:
        route_servers, _ = await aio_get_json(
            client, base_url + '/routeservers', key='routeservers'
        )
        if group:
            route_servers = [r for r in route_servers if r['group'] == group]

        rs_neighbors = await _query_rs_neighbors(base_url, client, route_servers)

        tasks = []
        for peers, metadata in rs_neighbors:
            for peer in peers:
                if peer['state'] != 'up':
                    continue
                url = f'{base_url}/routeservers/{metadata["route_server"]}/neighbors/{peer["id"]}/routes'
                peer_request_metadata = {
                    'peer_ip': peer['address'],
                    'peer_as': peer['asn'],
                    'route_server': metadata['route_server'],
                }
                task = aio_get_json(client, url, key='imported', metadata=peer_request_metadata)
                tasks.append(asyncio.ensure_future(task))

        for result in asyncio.as_completed(tasks):
            imported_routes, metadata = await result
            for imported_route in imported_routes:
                communities = (
                    imported_route['bgp']['communities']
                    + imported_route['bgp']['large_communities']
                )
                communities_set = {
                    ':'.join([str(segment) for segment in community]) for community in communities
                }
                route_entry = RouteEntry(
                    origin=imported_route['bgp']['as_path'][-1],
                    aspath=' '.join([str(asn) for asn in imported_route['bgp']['as_path']]),
                    prefix=imported_route['network'],
                    peer_ip=metadata['peer_ip'],
                    peer_as=metadata['peer_as'],
                    communities=communities_set,
                    source=f'Alice route server {metadata["route_server"]}',
                )
                yield route_entry


async def _query_rs_neighbors(
    base_url: str, client: aiohttp.ClientSession, route_servers: List[Dict[str, str]]
):
    tasks = []
    for route_server in route_servers:
        url = f'{base_url}/routeservers/{route_server["id"]}/neighbors'
        task = aio_get_json(
            client, url, key='neighbours', metadata={'route_server': route_server['id']}
        )
        tasks.append(asyncio.ensure_future(task))
    return await asyncio.gather(*tasks)
