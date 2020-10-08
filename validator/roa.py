import json
from typing import IO, Tuple

import radix


def parse_roas(roa_file: IO[bytes]) -> Tuple[radix.Radix, int]:
    roa_count = 0
    tree = radix.Radix()
    data = json.load(roa_file)
    for roa in data["roas"]:
        node = tree.add(roa["prefix"])
        if "roas" not in node.data:
            node.data["roas"] = list()
        node.data["roas"].append(
            {
                "asn": int(roa["asn"].replace("AS", "")),
                "max_length": roa["maxLength"],
            }
        )
        roa_count += 1
    return tree, roa_count
