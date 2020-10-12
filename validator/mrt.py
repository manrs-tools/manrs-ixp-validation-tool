from typing import IO, Generator, Iterable, Optional, Tuple

from ryu.lib import mrtlib
from ryu.lib.packet import bgp

from .status import RouteEntry

RIB_MESSAGES_V1 = (
    mrtlib.TableDumpAfiIPv4MrtMessage,
    mrtlib.TableDumpAfiIPv6MrtMessage,
)

RIB_MESSAGES_V2 = (
    mrtlib.TableDump2RibIPv4UnicastMrtMessage,
    mrtlib.TableDump2RibIPv6UnicastMrtMessage,
)


def parse_mrt(mrt_file: IO[bytes]) -> Generator[RouteEntry, None, None]:
    """
    Parse an MRT file and return a generator of RouteEntry's with
    details of all routes in the file.
    """
    peers = []
    for record in mrtlib.Reader(mrt_file):
        if isinstance(record.message, mrtlib.TableDump2PeerIndexTableMrtMessage):
            peers = record.message.peer_entries
        elif isinstance(record.message, RIB_MESSAGES_V2):
            for entry in record.message.rib_entries:
                origin, aspath = extract_aspath_info(entry.bgp_attributes)

                yield RouteEntry(
                    origin=origin,
                    aspath=aspath,
                    prefix=record.message.prefix.prefix,
                    prefix_length=record.message.prefix.length,
                    peer_ip=peers[entry.peer_index].ip_addr,
                    peer_as=peers[entry.peer_index].as_num,
                )
        elif isinstance(record.message, RIB_MESSAGES_V1):
            origin, aspath = extract_aspath_info(record.message.bgp_attributes)
            yield RouteEntry(
                origin=origin,
                aspath=aspath,
                prefix=record.message.prefix + "/" + str(record.message.prefix_len),
                prefix_length=record.message.prefix_len,
                peer_ip=record.message.peer_ip,
                peer_as=record.message.peer_as,
            )
        else:  # pragma: no cover
            print(f"Unknown MRT record, ignoring: {record}")


def extract_aspath_info(
    bgp_attributes: Iterable[bgp._PathAttribute],
) -> Tuple[Optional[int], str]:
    """
    Extract the origin AS and AS path string from a ryu AS path attribute.
    Returns a tuple of the origin AS and a string representing the
    full path. Origin may be None if the path is empty or the origin is
    an AS set. Path may be an empty string.
    """
    origin = None
    aspath_str = ""
    aspath = None
    as4path = None
    for attribute in bgp_attributes:
        if isinstance(attribute, bgp.BGPPathAttributeAsPath):
            if attribute.value:
                aspath = attribute.value
        if isinstance(attribute, bgp.BGPPathAttributeAs4Path):
            if attribute.value:
                as4path = attribute.value

    if aspath and as4path and len(as4path):
        n = len(aspath) - len(as4path)
        aspath = aspath[:n] + as4path

    if aspath:
        last_segment = aspath[-1]
        if isinstance(last_segment, list):
            origin = last_segment[-1]

        for segment in aspath:
            if isinstance(segment, list):
                aspath_str += " ".join([str(asn) for asn in segment])
            if isinstance(segment, set):
                aspath_str += " " + str(segment) + " "
    return origin, aspath_str.strip()
