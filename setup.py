#!/usr/bin/python3

import os.path
import warnings

from setuptools import setup


def relate_to_root(rel_path: str) -> str:
    here = os.path.abspath(os.path.dirname(__file__))
    return os.path.join(here, rel_path)


file_spec = [
    ("share/man/man1", ["data/video-dl.1.gz"]),
    ("share/man/man5", ["data/VideoDL.conf.5.gz"]),
]
data_files = []
for dest_dir, files in file_spec:
    present_files = []
    for filename in files:
        if os.path.exists(relate_to_root(filename)):
            present_files.append(filename)
        else:
            warnings.warn(
                f"File {filename} is not present! Try running 'make' first.",
                stacklevel=2,
            )
    if present_files:
        data_files.append((dest_dir, files))


setup(data_files=data_files)
