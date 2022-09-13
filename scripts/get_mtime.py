#!/usr/bin/env python3
#
# usage: get_mtime.py *file* [*file*...]
#
# Print the modification date of the most recently modified file in YAML format.

import os
import sys
import time


def main():
    mtime = max(os.stat(filename).st_mtime for filename in sys.argv[1:])
    date = time.strftime("%Y-%m-%d", time.gmtime(mtime))
    print(f"date: {date}")


if __name__ == "__main__":
    sys.exit(main())
