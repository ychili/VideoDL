#!/usr/bin/env python3
#
# usage: get_version.py *python_src*

import sys


def get_version(reader):
    for line in reader:
        if line.startswith("__version__"):
            delim = '"' if '"' in line else "'"
            return line.split(delim)[1]
    raise RuntimeError("Unable to find version string.")


def main():
    with open(sys.argv[1]) as file:
        ver = get_version(file)
    print(f"footer: VideoDL {ver}")


if __name__ == "__main__":
    sys.exit(main())
