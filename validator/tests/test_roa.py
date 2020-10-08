from pathlib import Path

from ..roa import parse_roas


def test_parse_roas():
    # Small ROA sample file, set to partially match the sample MRT file
    roa_file = Path(__file__).parent / "roa_test.json"
    with open(roa_file, "rb") as f:
        tree, count = parse_roas(f)

    assert 5 == count
    assert {
        "185.186.79.0/24",
        "185.186.11.0/24",
        "2001:db8::/32",
        "2001:db8::/33",
    } == set(tree.prefixes())

    node_data_v4 = list(tree.search_covered("185.186.79.0/24"))[0].data["roas"]
    assert [
        {"asn": 64496, "max_length": 28},
        {"asn": 64497, "max_length": 24},
    ] == node_data_v4

    node_data_v6_32 = tree.search_best("2001:db8::/32").data["roas"]
    assert [{"asn": 64498, "max_length": 64}] == node_data_v6_32

    node_data_v6_33 = tree.search_best("2001:db8::/33").data["roas"]
    assert [{"asn": 0, "max_length": 64}] == node_data_v6_33
