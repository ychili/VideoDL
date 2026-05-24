#!/usr/bin/env python3
#
# usage: get_version.py [*python_src*...]

from __future__ import annotations

import fileinput
from collections.abc import Iterable


def get_version(reader: Iterable[str]) -> str:
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
