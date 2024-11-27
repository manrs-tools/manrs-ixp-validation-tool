# MANRS IXP validation tool

This tool validates the routes seen in an MRT RIB dump, [Alice-LG](https://github.com/alice-lg/alice-lg) instance,
or [Bird's Eye](https://github.com/inex/birdseye) instance, against RPKI data, to see whether the RIB contains any RPKI
invalid routes. The purpose of this tool is to validate RPKI filtering on IXP route servers, by validating the routes
seen by the route server.

This tool was commissioned by [ISOC](https://www.internetsociety.org/) for the [MANRS](https://manrs.org/) project
and developed by [DashCare](https://www.dashcare.nl).

## Installation

This tool is compatible with Python 3.9 or newer. To run the tool, first install the requirements:

```shell
pip install -r requirements.txt
```

You may want to create a virtualenv for this first.

If you want to read MRT RIB dumps, you also need a recent install of [bgpdump](https://github.com/RIPE-NCC/bgpdump/).

## Running

The tool supports reading routes from different sources. To see all the
command line options, run:

```shell
validator/run.py -h
```

For example, to read from an MRT file:

```shell
validator/run.py --mrt-file <MRT file path> <ROA JSON file path>
```

The ROA JSON path is required for all sources, and must be a JSON file as produced by the RIPE NCC RPKI validator JSON
export, rpki-client (with `-j`), and others.

Some MRT dumps will include RPKI invalid routes in the RIB, but tagged with a specific community. To allow these routes,
supply the expected community with the `--communities-expected-invalid` parameter, e.g.:

```shell
validator/run.py --communities-expected-invalid 64500:1 --birdseye-url https://lg.example.net/route-server-name/api/ <ROA JSON file path>
```

You can set multiple communities, comma separated. When running in verbose mode, these routes are reported as RPKI
status `invalid_expected`, i.e. they were found in the RIB and are RPKI invalid, but this was expected due to the
communities set on the route, and is not an error.

The three possible input sources are:

- An MRT file, which must be a table dump v1/v2 RIB export. The path is provided with `--mrt_file`. You can provide a
  custom path to the `bgpdump` binary in `--path-bgpdump`
- An [Alice-LG](https://github.com/alice-lg/alice-lg) looking glass instance. Provide the URL in `--alice-url`, e.g.
  `--alice-url https://lg.example.net/api/v1/`. By default, this will collect all routes from all route servers
  configured in Alice-LG. Optionally, you can filter for a specific group with `--alice-rs-group`. You can check the
  available route server groups in the API yourself, e.g. on: `https://lg.example.net/api/v1/routeservers`. Alice-LG
  provides information on the expected community for RPKI invalids, and the tool will read, report and use this value.
  You can still override this with the `--communities-expected-invalid` parameter.
- A [Bird's Eye](https://github.com/inex/birdseye) looking glass instance. Provide the URL in `--birdseye-url`, e.g.
  `https://lg.example.net/<route-server-name>/api/`. The Bird's Eye API only allows querying one route server at a time,
  unlike Alice-LG. Note that the [IXP Manager](https://www.ixpmanager.org/) looking glass is not compatible, as
  its [API passthrough is limited to certain queries](https://docs.ixpmanager.org/features/looking-glass/#looking-glass-pass-thru-api-calls)
  and therefore it\'s not possible to read all routes from it.

By default, the tool will print a few statistics and details of all invalid prefixes, to stdout. If you add `-v` or
`--verbose`, it will print details on every route and it\'s status.

NOTE: in order to validate whether an MRT dump contained routes that were RPKI invalid at the time, the ROA JSON file
and MRT dump should be from around the same time. Using a much newer ROA file may result in false positives, flagging
routes that were valid at the time of the dump. When reading routes from an API, ensure your ROA JSON file is recent.

## Docker

The prebuilt Docker image uses `validator/run.py` as its entrypoint, enabling you to use it like this:

```shell
docker run ghcr.io/manrs-tools/manrs-ixp-validation-tool:latest -h
```

## Development

First, install the development requirements:

```shell
pip install -r requirements-dev.txt
```

Then, you can run the tests with `pytest`, or with coverage measurement:

```shell
pytest --cov-report term-missing:skip-covered --cov=validator
```

This project has 100% test coverage, except for specific exclusions.

MyPy and flake8 are used for typing and style checking:

```shell
flake8 validator mypy validator --ignore-missing-imports
```

A small MRT RIB dump and ROA JSON file are included in
`validator/tests/`.