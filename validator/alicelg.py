import aiohttp
from aiohttp_retry import RetryClient, ExponentialRetry
import asyncio
from typing import Any, Optional

from validator.status import RouteEntry


async def aio_get_json(client: aiohttp.ClientSession, url: str, key: Optional[str] = None, metadata: Any = None):
    print(f'req {url}')
    async with client.get(url) as resp:
        json = await resp.json()
        print(f'done {url}')
        if key:
            return json[key], metadata
        return json, metadata


async def get_rpki_invalid_community(client: aiohttp.ClientSession, base_url: str):
    json, _ = await aio_get_json(client, base_url + '/config')
    return ':'.join(json['rpki']['invalid'])


async def get_routes(base_url: str, group: Optional[str] = None):
    connector = aiohttp.TCPConnector(limit=10)
    async with RetryClient(connector=connector, raise_for_status=False) as client:
        rpki_invalid_community = await get_rpki_invalid_community(client, base_url)
        print(f'Found RPKI invalid community {rpki_invalid_community}')
        route_servers, _ = await aio_get_json(client, base_url + '/routeservers', key='routeservers')
        if group:
            route_servers = [r for r in route_servers if r['group'] == group]
        print(f'Found route servers {route_servers}')

        tasks = []
        for route_server in route_servers:
            url = f'{base_url}/routeservers/{route_server["id"]}/neighbors'
            task = aio_get_json(client, url, key='neighbours', metadata={'route_server': route_server['id']})
            tasks.append(asyncio.ensure_future(task))
        route_servers_peers = await asyncio.gather(*tasks)

        tasks = []
        for peers, metadata in route_servers_peers:
            for peer in peers:
                if peer['state'] != 'up':
                    continue
                try:
                    url = f'{base_url}/routeservers/{metadata["route_server"]}/neighbors/{peer["id"]}/routes'
                except KeyError:
                    print('----')
                    print(str(peers)[:50])
                    print(metadata)
                    print('----')
                    raise
                peer_request_metadata = {
                    'peer_ip': peer['address'],
                    'peer_as': peer['asn'],
                    'route_server': metadata['route_server'],
                }
                task = aio_get_json(client, url, key='imported', metadata=peer_request_metadata)
                tasks.append(asyncio.ensure_future(task))

        route_count = 0
        for result in asyncio.as_completed(tasks):
            imported_routes, metadata = await result
            for imported_route in imported_routes:
                communities = imported_route['bgp']['communities'] + imported_route['bgp']['large_communities']
                communities_set = {
                    ':'.join([str(segment) for segment in community])
                    for community in communities
                }
                route_entry = RouteEntry(
                    origin=imported_route['bgp']['as_path'][-1],
                    aspath=' '.join([str(asn) for asn in imported_route['bgp']['as_path']]),
                    prefix=imported_route['network'],
                    peer_ip=metadata['peer_ip'],
                    peer_as=metadata['peer_as'],
                    communities=communities_set,
                    source=f'Route server {metadata["route_server"]}',
                )
                yield route_entry
                route_count += 1
            print(f'processed {metadata}, now {route_count} total')
        print(route_count)

if __name__ == "__main__":  # pragma: no cover
    loop = asyncio.get_event_loop()
    loop.run_until_complete(get_routes('https://lg.ecix.net/api/v1/'))
    loop.close()
