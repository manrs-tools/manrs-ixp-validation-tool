#!/usr/bin/env python
# flake8: noqa: E402
import argparse
import asyncio
import sys
from pathlib import Path
from typing import Optional, Set

root = str(Path(__file__).resolve().parents[1])
sys.path.append(root)

from validator.mrt import parse_mrt
from validator.roa import parse_roas
from validator.status import RPKIStatus
from validator.validate import validate


async def run(
    mrt_file: str,
    roa_file: str,
    path_bgpdump: Optional[str],
    communities_expected_invalid: Set[str],
    verbose: bool,
):
    """
    Main runner method. Reads from mrt_file and roa_file, outputs to stdout.
    """
    invalid_count = 0
    mrt_entry_count = 0

    with open(roa_file, "rb") as f:
        roa_tree, roa_count = parse_roas(f)

    for mrt_entry in parse_mrt(mrt_file, path_bgpdump):
        mrt_entry_count += 1
        result = validate(mrt_entry, roa_tree, communities_expected_invalid, verbose=verbose)
        if result:
            print(validator_result_str(result))
            if result["status"] == RPKIStatus.invalid:
                invalid_count += 1
    print(
        f"Processed {mrt_entry_count} MRT entries, {roa_count} ROAs, "
        f"found {invalid_count} unexpected RPKI invalid entries"
    )


def validator_result_str(result) -> str:
    """
    Translate a single validation result dictionary to a user-friendly
    string with validation status and details of the route and ROAs.
    """
    communities_str = (
        " ".join(sorted(result["route"]["communities"]))
        if result["route"]["communities"]
        else "<none>"
    )
    output = (
        f"RPKI {result['status'].name}: prefix {result['route']['prefix']} from "
        f"origin AS{result['route']['origin']}\n"
        f"Received from peer {result['route']['peer_ip']} AS{result['route']['peer_as']}\n"
        f"AS path {result['route']['aspath']}\n"
        f"Communities {communities_str}\n"
    )
    if result["roas"]:
        output += "ROAs found:\n"
        for roa in result["roas"]:
            output += f"    Prefix {roa['prefix']}, ASN {roa['asn']}, max length {roa['max_length']}\n"
    else:
        output += "No ROAs found\n"
    return output


def main():  # pragma: no cover
    description = """Validate data in an MRT RIB against RPKI data."""
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument(
        "-v",
        "--verbose",
        dest="verbose",
        action="store_true",
        help="output validation details for all routes, instead of only invalids",
    )
    parser.add_argument(
        "-p",
        "--path-bgpdump",
        dest="path_bgpdump",
        action="store",
        help="path to the bgpdump binary from libbgpdump (default: 'bgpdump', expected in $PATH)",
    )
    parser.add_argument(
        "-c",
        "--communities-expected-invalid",
        dest="communities_expected_invalid",
        action="store",
        help="communities expected on RPKI invalid routes, comma separated - RPKI invalid routes "
        "with one of these communities, will not be reported as an error",
    )
    parser.add_argument(dest="mrt_file", type=str, help=f"path to MRT file")
    parser.add_argument(dest="roa_file", type=str, help=f"path to ROAs in JSON format")
    args = parser.parse_args()

    communities_expected_invalid = set()
    if args.communities_expected_invalid:
        communities_expected_invalid = set(args.communities_expected_invalid.split(","))

    loop = asyncio.get_event_loop()
    loop.run_until_complete(run(
        args.mrt_file,
        args.roa_file,
        args.path_bgpdump,
        communities_expected_invalid,
        args.verbose,
    ))
    loop.close()


if __name__ == "__main__":  # pragma: no cover
    main()
