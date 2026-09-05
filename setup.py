#!/usr/bin/python3

from __future__ import annotations

import pathlib
import warnings
from collections.abc import Sequence
from typing import TYPE_CHECKING

from setuptools import setup

if TYPE_CHECKING:
    from _typeshed import StrPath


def relate_to_root(rel_path: StrPath) -> pathlib.Path:
    here = pathlib.Path(__file__).parent.resolve()
    return here / rel_path


file_spec = [
    ("share/man/man1", ["data/video-dl.1.gz"]),
    ("share/man/man5", ["data/VideoDL.conf.5.gz"]),
]
data_files: list[tuple[str, Sequence[str]]] = []
for dest_dir, files in file_spec:
    present_files = []
    for filename in files:
        if relate_to_root(filename).exists():
            present_files.append(filename)
        else:
            warnings.warn(
                f"File {filename} is not present! Try running 'make' first.",
                stacklevel=2,
            )
    if present_files:
        data_files.append((dest_dir, present_files))


setup(data_files=data_files)
