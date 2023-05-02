NAME
====

video-dl - video download manager for yt-dlp

SYNOPSIS
========

.. include:: include/SYNOPSIS.rst

DESCRIPTION
===========

**video-dl** embeds the **yt-dlp**\ (1) video downloader and facilitates
non-interactive or periodic downloads. It loads an INI-style
configuration file (or files) containing all the information it needs to
manage the download. See **VideoDL.conf**\ (5) for the format of this
file.

**video-dl** *job-identifier* will perform the download job specified in
the *job-identifier* section of the loaded configuration. If
*job-identifier* is omitted, it performs all jobs in all sections. A job
that fails or cannot be successfully performed will be skipped and the
next tried.

OPTIONS
=======

.. include:: include/OPTIONS.rst

EXIT STATUS
===========

**video-dl** will exit with status 100 if it is unable to find any
configuration file. Otherwise it will log warnings and errors to
standard error (and to file if your configuration requests it), skipping
programs with errors and exiting normally.

FILES
=====

If the **--config** option is omitted, **video-dl** will search for
configuration files in the following locations:

*/etc/VideoDL.conf*
   System wide configuration file. See **VideoDL.conf**\ (5) for the
   format of this file.

*${XDG_CONFIG_HOME}/VideoDL/* or *${HOME}/.config/VideoDL/*
   Per user configuration file directory. See **VideoDL.conf**\ (5) for
   the format of files in this directory.
   Files in this directory can use any name, but only the
   file *default.conf* will be read if no custom filename is passed to
   **--config**.

*${HOME}/.VideoDL.conf*
   Alternate per user configuration file. See **VideoDL.conf**\ (5) for
   the format of this file.

*./VideoDL.conf*
   Current directory configuration file. See **VideoDL.conf**\ (5) for
   the format of this file.

All files, if they exist, will be read in the above order. Any
conflicting keys are taken from the more recent configuration while the
previously existing keys are retained.

SEE ALSO
========

**VideoDL.conf**\ (5), **yt-dlp**\ (1)
