#!/usr/bin/env python3
#
# usage: get_version.py [*python_src*...]

from __future__ import annotations

import fileinput
from collections.abc import Iterable


def get_version(reader: Iterable[str]) -> str:
    """Extract version string from an iterable of lines.

    >>> get_version(["__version__='0.0.0'\\n"])
    '0.0.0'
    >>> get_version(["  __version__='0.0.0'\\n"]) # Can't indent
    Traceback (most recent call last):
        ...
    RuntimeError: Unable to find version string.
    >>> get_version(["__version__=0.0.0\\n"]) # Value must be quote delimited
    Traceback (most recent call last):
        ...
    IndexError: list index out of range
    """
    for line in reader:
        if line.startswith("__version__"):
            delim = '"' if '"' in line else "'"
            return line.split(delim)[1]
    msg = "Unable to find version string."
    raise RuntimeError(msg)


def main() -> None:
    file = fileinput.input(encoding="utf-8")
    ver = get_version(file)
    print(f"footer: VideoDL {ver}")


if __name__ == "__main__":
    main()
