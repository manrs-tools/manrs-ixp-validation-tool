import textwrap
from pathlib import Path

import pytest

from ..run import run


@pytest.mark.asyncio
async def test_integration(capsys):
    # By calling the runner, this serves as the integration test
    mrt_file = Path(__file__).parent / "185.186.nlix.mrt"
    roa_file = Path(__file__).parent / "roa_test.json"

    await run(
        roa_file=roa_file,
        verbose=False,
        communities_expected_invalid=set(),
        path_bgpdump=None,
        mrt_file=mrt_file,
        alice_url=None,
        alice_rs_group=None,
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

        Processed 23 route entries, 5 ROAs, found 1 unexpected RPKI invalid entries"""
    ).strip()
    assert expected == output.out.strip()

    await run(
        roa_file=roa_file,
        verbose=True,
        communities_expected_invalid=set(),
        path_bgpdump=None,
        mrt_file=mrt_file,
        alice_url=None,
        alice_rs_group=None,
    )
    output = capsys.readouterr()
    assert "RPKI valid: prefix 185.186.11.0/24 from origin AS26695" in output.out
