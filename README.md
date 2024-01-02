VideoDL is a video download manager.
It wraps the `yt-dlp` video downloader program and facilitates
non-interactive or periodic downloads.
It loads an INI-style configuration file (or files) in which each section
contains the parameters for one download job.
One or more jobs can be executed by passing arguments to the command-line
interface, `video-dl`.

# Motivation

To quote from [TheFrenchGhosty’s Ultimate YouTube DL Scripts
Collection 3.1.1][0]:

> Downloading and archiving YouTube content is complicated, especially
> because YouTube sometimes can take days to transcode videos to the
> best quality. A workaround to this issue is to have a script that will
> download everything that came out 30 days ago (and before) and, to
> avoid missing videos takedown/delete, have a script that will download
> everything created in the last 30 days potentially in a quality that’s
> not the best.

> Considering that I chose to separate the content:

> **Archivist Scripts**: Scripts that will download everything that was
> created before the current date, minus 30 days. For example, if the
> current date is 2021-01-30, everything created **before** 2021-01-01
> will be downloaded. This is needed because YouTube takes time to
> transcode videos (usually 1 week but sometimes more, the script assume
> it will take a maximum of 1 month).

> **Recent Scripts**: Scripts that will download everything that was
> created the current date, minus 30 days. For example, if the current
> date is 2021-01-30, everything created **after** 2021-01-01 will be
> downloaded, it won’t necessarily download the best possible quality
> since YouTube sometimes takes days to weeks to process videos, however
> it’s useful to have in case videos get takedown by YouTube or their
> author in the first month.

Thus arose the need to run YouTube DL as a cron or anacron job.
However issues were encountered when saving videos to an external disk drive
that may or may not be connected to the computer when the job was run.
So a layer of error logging was added to the download script.
That script eventually evolved into this script.

[0]: https://github.com/TheFrenchGhosty/TheFrenchGhostys-Ultimate-YouTube-DL-Scripts-Collection/blob/master/docs/Scripts-Type.md

# Requirements

Run-time dependencies:

  - Python 3.8+
  - [yt-dlp][1]
  - [PyYAML][2] *(Optional)* - if this is installed, you can write your
    options file in YAML format as well as standard JSON.

To build the documentation:

  - `make`, `sh`, `gzip`
  - [Pandoc][3]

[1]: https://github.com/yt-dlp/yt-dlp/
[2]: https://pyyaml.org/
[3]: https://pandoc.org/

# Usage

Usage and config file format are described in the documentation.
See some example files in the [examples directory](examples),
and see the manual(s) in the data directory.

# Documentation

Documentation sources are in reStructuredText format
and reside in the [docs directory](docs).
The makefile contains recipes for converting these to complete manuals
along with the needed metadata using Pandoc.
The result should be two man pages for Unix users
and one plain-text manual that summarizes these.
The man pages are divided into `video-dl.1` for the command-line interface
and `VideoDL.conf.5` for the configuration file format.

# Copyright

Copyright 2022-2024 Dylan Maltby

This program is free software: you can redistribute it and/or modify it
under the terms of the GNU General Public License as published by the
Free Software Foundation, either version 3 of the License, or (at your
option) any later version.

This program is distributed in the hope that it will be useful, but
WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General
Public License for more details.

You should have received a copy of the GNU General Public License along
with this program. If not, see <https://www.gnu.org/licenses/>.
