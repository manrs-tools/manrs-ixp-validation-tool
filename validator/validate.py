import dataclasses
from typing import Dict, List, Optional, Union

import radix

from .status import RouteEntry, RPKIStatus


def validate(
    route: RouteEntry, roa_tree: radix.Radix, return_all=False
) -> Optional[
    Dict[
        str,
        Union[RPKIStatus, Dict[str, Union[str, int]], List[Dict[str, Union[str, int]]]],
    ]
]:
    rnodes = roa_tree.search_covering(route.prefix)
    status = RPKIStatus.invalid
    if not rnodes:
        status = RPKIStatus.not_found
    for rnode in rnodes:
        for roa in rnode.data["roas"]:
            if (
                route.origin
                and route.origin == roa["asn"]
                and route.prefix_length <= roa["max_length"]
            ):
                status = RPKIStatus.valid
    if status == RPKIStatus.invalid or return_all:
        roa_dicts = []
        for rnode in rnodes:
            for roa in rnode.data["roas"]:
                roa_dicts.append(
                    {
                        "prefix": rnode.prefix,
                        "asn": roa["asn"],
                        "max_length": roa["max_length"],
                    }
                )
        return {
            "status": status,
            "route": dataclasses.asdict(route),
            "roas": roa_dicts,
        }
    return None
