MANRS IXP validation tool
=========================

This tool validates the data in an MRT RIB dump against RPKI data,
to see whether the RIB contains any RPKI invalid routes.
The purpose of this tool is to validate RPKI filtering on IXP route
servers, by validating a RIB dump from the route server.

This tool was commissioned by ISOC_ for the MANRS_ project and
developed by DashCare_.

.. _ISOC: https://www.internetsociety.org/
.. _MANRS: https://www.manrs.org/
.. _DashCare: https://www.dashcare.nl

Running
-------
This tool is compatible with Python 3.6 or newer.
To run the tool, first install the requirements::

    pip install -r requirements.txt

You may want to create a virtualenv for this first.

You also need a recent install of bgpdump_.

.. _bgpdump: https://github.com/RIPE-NCC/bgpdump/

Then, run with::

    validator/run.py <MRT file path> <ROA JSON file path>

The MRT file should be a table dump v1/v2 RIB export.
The ROA JSON path is a JSON file as produced by the RIPE NCC RPKI validator
JSON export, rpki-client (with ``-j``), and others.

By default, the tool will print a few statistics and details of all invalid
prefixes, to stdout. If you add ``-v`` or ``--verbose``, it will print details
on every prefix seen in the MRT file. You can also set a custom path to the
bgpdump library. Use the ``-h`` flag to see all options.

NOTE: in order to validate whether or not an MRT dump contained routes that
were RPKI invalid at the time, the ROA JSON file and MRT dump should be from
around the same time. Using a much newer ROA file may result in false
positives, flagging routes that were valid at the time of the dump.

Development
-----------
First, install the development requirements::

    pip install -r requirements-dev.txt

Then, you can run the tests with ``pytest``, or with coverage measurement::

    pytest --cov-report term-missing:skip-covered --cov=validator

This project has 100% test coverage, except for specific exclusions.

MyPy and flake8 are used for typing and style checking::

    flake8 validator
    mypy validator --ignore-missing-imports

A small MRT RIB dump and ROA JSON file are included in ``validator/tests/``.
