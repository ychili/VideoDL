#!/usr/bin/env python3
#
# usage: convert_time.py [*file*...]
#
# For each line of *file* (or standard input) containing a Unix timestamp,
# print the most recent timestamp in YAML format.

import fileinput
import time


def main() -> None:
    timestamp = max(float(line) for line in fileinput.input(encoding="utf-8"))
    date = time.strftime("%Y-%m-%d", time.gmtime(timestamp))
    print(f"date: {date}")


if __name__ == "__main__":
    main()
