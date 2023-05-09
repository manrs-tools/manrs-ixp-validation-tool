from validator.utils import get_data_from_json


def test_return_specified_key():
    data = get_data_from_json({"foo": "bar"}, ["foo"])

    assert data == "bar"


def test_return_all_data_if_no_key_specified():
    data = get_data_from_json({"foo": "bar"})

    assert data == {"foo": "bar"}


def test_return_first_key_if_it_exists():
    data = get_data_from_json({"foo": "bar"}, ["foo", "baz"])

    assert data == "bar"


def test_return_second_key_if_first_key_does_not_exist():
    data = get_data_from_json({"foo": "bar"}, ["baz", "foo"])

    assert data == "bar"


def test_return_none_if_no_provided_keys_exist():
    data = get_data_from_json({"foo": "bar"}, ["baz", "no-key"])

    assert data is None
