# flake8: noqa: W293
import textwrap
from pathlib import Path

import pytest
from aioresponses import aioresponses

from ..run import run
from . import test_alicelg, test_birdseye

ROA_FILE = Path(__file__).parent / "roa_test.json"


@pytest.mark.asyncio
async def test_integration_mrt(capsys):
    mrt_file = Path(__file__).parent / "185.186.nlix.mrt"

    await run(
        roa_file=ROA_FILE,
        verbose=False,
        communities_expected_invalid=set(),
        path_bgpdump=None,
        mrt_file=mrt_file,
        alice_url=None,
        alice_rs_group=None,
        birdseye_url=None,
    )
    output = capsys.readouterr()
    expected = textwrap.dedent(
        """
        RPKI invalid: prefix 185.186.79.0/24 from origin AS136258
        Received from peer: 193.239.116.255 AS34307
        AS path: 9009 136258
        Communities: 213279:34307:492 213279:9009:492 34307:52115 9009:50045 9009:55160 9009:888 9009:999
        ROAs found:
            Prefix 185.186.79.0/24, ASN 64496, max length 28
            Prefix 185.186.79.0/24, ASN 64497, max length 24

        Processed 23 route entries, 6 ROAs, found 1 unexpected RPKI invalid entries"""
    ).strip()
    assert expected == output.out.strip()

    await run(
        roa_file=ROA_FILE,
        verbose=True,
        communities_expected_invalid=set(),
        path_bgpdump=None,
        mrt_file=mrt_file,
        alice_url=None,
        alice_rs_group=None,
        birdseye_url=None,
    )
    output = capsys.readouterr()
    assert "RPKI valid: prefix 185.186.11.0/24 from origin AS26695" in output.out


@pytest.mark.asyncio
async def test_integration_alice(capsys):
    with aioresponses() as http_mock:
        test_alicelg.prepare_query_rpki_invalid_community(http_mock)
        test_alicelg.prepare_get_routes(http_mock)

        await run(
            roa_file=ROA_FILE,
            verbose=False,
            communities_expected_invalid=set(),
            path_bgpdump=None,
            mrt_file=None,
            alice_url="http://example.net/api/v1",
            alice_rs_group="group1",
            birdseye_url=None,
        )
    output = capsys.readouterr()
    expected = textwrap.dedent(
        """
        Using BGP communities 64501:10:20 as expected RPKI invalid
        Processed 2 route entries, 6 ROAs, found 0 unexpected RPKI invalid entries"""
    ).strip()
    assert expected == output.out.strip()

    with aioresponses() as http_mock:
        test_alicelg.prepare_query_rpki_invalid_community(http_mock)
        test_alicelg.prepare_get_routes(http_mock)

        await run(
            roa_file=ROA_FILE,
            verbose=False,
            communities_expected_invalid={"64501:999"},
            path_bgpdump=None,
            mrt_file=None,
            alice_url="http://example.net/api/v1",
            alice_rs_group="group1",
            birdseye_url=None,
        )
    output = capsys.readouterr()
    expected = textwrap.dedent(
        """
        Using BGP communities 64501:999 as expected RPKI invalid
        RPKI invalid: prefix 192.0.2.0/24 from origin AS64502
        Received from peer: 192.0.2.1 AS64501
        AS path: 64501 64502
        Communities: 64501:1 64501:10:20 64501:2
        Source: Alice LG route server server1 peer peer1
        ROAs found:
            Prefix 192.0.2.0/24, ASN 0, max length 24
        
        RPKI invalid: prefix 192.0.2.0/24 from origin AS64502
        Received from peer: 192.0.2.1 AS64501
        AS path: 64501 64502
        Communities: 64501:1 64501:10:20 64501:2
        Source: Alice LG route server server2 peer peer1
        ROAs found:
            Prefix 192.0.2.0/24, ASN 0, max length 24
        
        Processed 2 route entries, 6 ROAs, found 2 unexpected RPKI invalid entries"""
    ).strip()
    assert expected == output.out.strip()


@pytest.mark.asyncio
async def test_integration_birdseye(capsys):
    with aioresponses() as http_mock:
        test_birdseye.prepare_get_routes(http_mock)

        await run(
            roa_file=ROA_FILE,
            verbose=False,
            communities_expected_invalid=set(),
            path_bgpdump=None,
            mrt_file=None,
            alice_url=None,
            alice_rs_group=None,
            birdseye_url="http://example.net/api/",
        )
    output = capsys.readouterr()
    expected = textwrap.dedent(
        """
        RPKI invalid: prefix 192.0.2.0/24 from origin AS64502
        Received from peer: 192.0.2.1 AS64501
        AS path: 64501 64502
        Communities: 64501:1 64501:10:20 64501:2
        Source: Bird's Eye peer peer1
        ROAs found:
            Prefix 192.0.2.0/24, ASN 0, max length 24
        
        Processed 1 route entries, 6 ROAs, found 1 unexpected RPKI invalid entries"""
    ).strip()
    assert expected == output.out.strip()
