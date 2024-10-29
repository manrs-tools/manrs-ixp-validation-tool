import json
from typing import IO, Tuple

import radix


def parse_roas(roa_file: IO[bytes]) -> Tuple[radix.Radix, int]:
    """
    Parse the ROAs in roa_file, which should be a file handle on a ROA JSON.
    Returns a tuple of a radix tree that contains all ROAs, and the number
    of ROAs processed.
    """
    roa_count = 0
    tree = radix.Radix()
    data = json.load(roa_file)

    for roa in data["roas"]:
        node = tree.add(roa["prefix"])
        if "roas" not in node.data:
            node.data["roas"] = list()
        node.data["roas"].append(
            {
                "asn": int(str(roa["asn"]).replace("AS", "")),
                "max_length": roa["maxLength"],
            }
        )
        roa_count += 1

    return tree, roa_count
