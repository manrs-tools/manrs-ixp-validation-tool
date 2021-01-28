import subprocess
from typing import AsyncGenerator, Optional

from .status import RouteEntry


async def parse_mrt(
    mrt_file, path_bgpdump: Optional[str] = None
) -> AsyncGenerator[RouteEntry, None]:
    """
    Parse an MRT file and return a generator of RouteEntry's with
    details of all routes in the file.
    """
    if not path_bgpdump:
        path_bgpdump = "bgpdump"

    bgpdump = subprocess.run(
        [path_bgpdump, "-m", "-l", "-v", mrt_file],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if bgpdump.returncode:  # pragma: no cover
        raise Exception(
            f'Failed to parse MRT file with bgpdump: {bgpdump.stderr.decode("ascii")}'
        )

    for rib_entry_bytes in bgpdump.stdout.splitlines():
        rib_entry = rib_entry_bytes.decode("ascii").split("|")
        if len(rib_entry) == 16:
            # Normal case
            (
                dump_type,
                timestamp,
                entry_type,
                peer_ip,
                peer_as_str,
                prefix,
                aspath,
                bgp_origin,
                next_hop,
                local_pref,
                med,
                communities,
                extended_communities,
                _,
                _,
                _,
            ) = rib_entry
        elif len(rib_entry) == 17:  # pragma: no cover
            # BGP ADDPATH path id included
            (
                dump_type,
                timestamp,
                entry_type,
                peer_ip,
                peer_as_str,
                prefix,
                path_id,
                aspath,
                bgp_origin,
                next_hop,
                local_pref,
                med,
                communities,
                extended_communities,
                _,
                _,
                _,
            ) = rib_entry
        else:  # pragma: no cover
            print(
                f"Ignoring unexpected bgpdump output with {len(rib_entry)} fields: {rib_entry}"
            )
            continue

        peer_as = int(peer_as_str)
        communities_set = set()
        if communities:
            communities_set |= set(communities.split(" "))
        if extended_communities:
            communities_set |= set(extended_communities.split(" "))
        try:
            origin: Optional[int] = int(aspath.split(" ")[-1])
        except ValueError:
            origin = None

        yield RouteEntry(
            origin=origin,
            aspath=aspath,
            prefix=prefix,
            peer_ip=peer_ip,
            peer_as=peer_as,
            communities=communities_set,
        )
    if bgpdump.stderr:  # pragma: no cover
        print(f'Unparsed stderr output from bgpdump:\n{bgpdump.stderr.decode("ascii")}')
