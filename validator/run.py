#!/usr/bin/env python
# flake8: noqa: E402
import argparse
import asyncio
import sys
from pathlib import Path
from typing import Optional, Set

root = str(Path(__file__).resolve().parents[1])
sys.path.append(root)

from validator import alicelg, birdseye
from validator.mrt import parse_mrt
from validator.roa import parse_roas
from validator.status import RPKIStatus
from validator.validate import validate


async def run(
    roa_file: str,
    verbose: bool,
    communities_expected_invalid: Set[str],
    mrt_file: Optional[str],
    path_bgpdump: Optional[str],
    alice_url: Optional[str],
    alice_rs_group: Optional[str],
    birdseye_url: Optional[str],
):
    invalid_count = 0
    route_count = 0

    with open(roa_file, "rb") as f:
        roa_tree, roa_count = parse_roas(f)

    if mrt_file:
        routes_generator = parse_mrt(mrt_file, path_bgpdump)
    elif alice_url:
        if not communities_expected_invalid:
            alice_invalid_community = await alicelg.query_rpki_invalid_community(alice_url)
            if alice_invalid_community:
                communities_expected_invalid = {alice_invalid_community}
        routes_generator = alicelg.get_routes(alice_url, alice_rs_group)
    elif birdseye_url:
        routes_generator = birdseye.get_routes(birdseye_url)
    else:  # pragma: no cover
        raise Exception("Unable to determine route source")

    if communities_expected_invalid:
        print(
            f'Using BGP communities {", ".join(communities_expected_invalid)} '
            f"as expected RPKI invalid"
        )

    async for route_entry in routes_generator:
        route_count += 1
        result = validate(route_entry, roa_tree, communities_expected_invalid, verbose=verbose)
        if result:
            print(validator_result_str(result))
            if result["status"] == RPKIStatus.invalid:
                invalid_count += 1
    print(
        f"Processed {route_count} route entries, {roa_count} ROAs, "
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
        f"Received from peer: {result['route']['peer_ip']} AS{result['route']['peer_as']}\n"
        f"AS path: {result['route']['aspath']}\n"
        f"Communities: {communities_str}\n"
    )
    if result["route"].get("source"):
        output += f"Source: {result['route']['source']}\n"
    if result["roas"]:
        output += "ROAs found:\n"
        for roa in result["roas"]:
            output += (
                f"    Prefix {roa['prefix']}, ASN {roa['asn']}, max length {roa['max_length']}\n"
            )
    else:
        output += "No ROAs found\n"
    return output


def main():  # pragma: no cover
    description = """Validate routes from a route server against RPKI data."""
    epilog = """
    Alice LG instances may list the BGP communities expected on RPKI
    invalid routes through their API. If found, this is used as if provided
    through the --communities-expected-invalid parameter. If an Alice LG
    instance is queried and --communities-expected-invalid is provided,
    the communities found in the Alice LG configuration are ignored.
    """
    parser = argparse.ArgumentParser(description=description, epilog=epilog)
    source_group = parser.add_mutually_exclusive_group(required=True)
    parser.add_argument(dest="roa_file", type=str, help=f"path to ROAs in JSON format")
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Output validation details for all routes, instead of only invalids.",
    )
    parser.add_argument(
        "-c",
        "--communities-expected-invalid",
        help="Communities expected on RPKI invalid routes, comma separated - RPKI invalid routes "
        "with one of these communities, will not be reported as an error.",
    )
    source_group.add_argument(
        "-m",
        "--mrt-file",
        help="Read routes from an MRT file, by providing the path to this file",
    )
    parser.add_argument(
        "-p",
        "--path-bgpdump",
        help="Path to the bgpdump binary from libbgpdump (default: 'bgpdump', expected in $PATH).",
    )
    source_group.add_argument(
        "-a",
        "--alice-url",
        help="Read routes from an Alice Looking Glass API, by specifying the base URL e.g. "
        "'https://lg.example.net/api/v1/'",
    )
    parser.add_argument(
        "-g",
        "--alice-rs-group",
        help="Group to filter for in Alice LG instances with multiple route servers. Group names "
        "can be seen on 'https://lg.example.net/api/v1/routeservers/'",
    )
    source_group.add_argument(
        "-b",
        "--birdseye-url",
        help="Read routes from a Bird's eye Looking Glass API, by specifying the base URL e.g. "
        "'https://lg.example.net/<route-server-name>/api/'",
    )
    args = parser.parse_args()

    communities_expected_invalid = set()
    if args.communities_expected_invalid:
        communities_expected_invalid = set(args.communities_expected_invalid.split(","))

    loop = asyncio.get_event_loop()
    loop.run_until_complete(
        run(
            args.roa_file,
            args.verbose,
            communities_expected_invalid,
            args.mrt_file,
            args.path_bgpdump,
            args.alice_url,
            args.alice_rs_group,
            args.birdseye_url,
        )
    )
    loop.close()


if __name__ == "__main__":  # pragma: no cover
    main()
