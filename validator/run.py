#!/usr/bin/env python
# flake8: noqa: E402
import argparse
import sys
from pathlib import Path

root = str(Path(__file__).resolve().parents[1])
sys.path.append(root)

from validator.mrt import parse_mrt
from validator.roa import parse_roas
from validator.status import RPKIStatus
from validator.validate import validate


def run(mrt_file: str, roa_file: str, verbose: bool):
    invalid_count = 0
    mrt_entry_count = 0

    with open(roa_file, "rb") as f:
        roa_tree, roa_count = parse_roas(f)

    with open(mrt_file, "rb") as f:
        for mrt_entry in parse_mrt(f):
            mrt_entry_count += 1
            result = validate(mrt_entry, roa_tree, return_all=verbose)
            if result:
                if result["status"] == RPKIStatus.invalid:
                    invalid_count += 1
                print(validator_result_str(result))
    print(
        f"Processed {mrt_entry_count} MRT entries, {roa_count} ROAs, found {invalid_count} RPKI invalid entries"
    )


def validator_result_str(result) -> str:
    output = (
        f"RPKI {result['status'].name}: prefix {result['route']['prefix']} from "
        f"origin AS{result['route']['origin']}\n"
        f"Received from peer {result['route']['peer_ip']} AS{result['route']['peer_as']}\n"
        f"AS path {result['route']['aspath']}\n"
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
    parser.add_argument(dest="mrt_file", type=str, help=f"path to MRT file")
    parser.add_argument(dest="roa_file", type=str, help=f"path to ROAs in JSON format")
    args = parser.parse_args()
    run(args.mrt_file, args.roa_file, args.verbose)


if __name__ == "__main__":  # pragma: no cover
    main()
