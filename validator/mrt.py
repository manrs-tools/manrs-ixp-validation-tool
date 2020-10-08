from typing import IO, Generator, Optional, Tuple

from ryu.lib import mrtlib
from ryu.lib.packet import bgp

from .status import RouteEntry


def parse_mrt(mrt_file: IO[bytes]) -> Generator[RouteEntry, None, None]:
    peers = []
    for record in mrtlib.Reader(mrt_file):
        if isinstance(record.message, mrtlib.TableDump2PeerIndexTableMrtMessage):
            peers = record.message.peer_entries
        elif isinstance(
            record.message,
            (
                mrtlib.TableDump2RibIPv4UnicastMrtMessage,
                mrtlib.TableDump2RibIPv6UnicastMrtMessage,
            ),
        ):
            prefix = record.message.prefix.prefix
            prefix_length = record.message.prefix.length
            for entry in record.message.rib_entries:
                origin = None
                aspath = ""
                for attribute in entry.bgp_attributes:
                    if isinstance(attribute, bgp.BGPPathAttributeAsPath):
                        origin, aspath = extract_aspath_info(attribute)

                yield RouteEntry(
                    origin=origin,
                    aspath=aspath,
                    prefix=prefix,
                    prefix_length=prefix_length,
                    peer_ip=peers[entry.peer_index].ip_addr,
                    peer_as=peers[entry.peer_index].as_num,
                )
        else:  # pragma: no cover
            print(f"Unknown MRT record, ignoring: {record}")


def extract_aspath_info(
    attribute: bgp.BGPPathAttributeAsPath,
) -> Tuple[Optional[int], str]:
    origin = None
    aspath = ""

    if attribute.value:
        last_segment = attribute.value[-1]
        if isinstance(last_segment, list):
            origin = last_segment[-1]

        for segment in attribute.value:
            if isinstance(segment, list):
                aspath += " ".join([str(asn) for asn in segment])
            if isinstance(segment, set):
                aspath += " " + str(segment) + " "
    return origin, aspath.strip()
