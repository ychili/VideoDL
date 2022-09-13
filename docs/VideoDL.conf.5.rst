NAME
====

VideoDL.conf - VideoDL configuration file

DESCRIPTION
===========

This file format is used by **video-dl**\ (1) to manage its downloads.
The file format follows INI file syntax comprising key-value pairs
within sections. Each section in the file constitutes one download job
which can be started from the command line.
The *job-identifier* is the section name.

The INI file syntax is made up of key-value pairs within sections.
Briefly,

   Sections are led by a [section] header, followed by key/value
   entries separated by '=' or ':'. Section names are case sensitive
   but keys are not. Leading and trailing whitespace is removed from
   keys and values. Files may include comments, prefixed by the
   characters '#' or ';'.

Extended Interpolation is enabled. Use '${section:option}' to denote a
value from a foreign section. If the 'section:' part is omitted,
interpolation defaults to the current section (and possibly the default
values from the section 'DEFAULT'). This does mean that the literal
character '$' needs to be escaped as '$$'.

Every section must contain all required keys, plus any optional keys.
Unrecognized keys will be ignored.
All sections will inherit values from the section named 'DEFAULT', if
it exists.

.. include:: docs/include/CONFIGKEYS.rst

FILES
=====

*/etc/VideoDL.conf*
   System wide configuration file.

*${XDG_CONFIG_HOME}/VideoDL/* or *${HOME}/.config/VideoDL/*
   Per user configuration file directory.
   The default configuration file for this directory is *default.conf*.
   It may contain other files which are selectable
   by the **--config** option (see **video-dl**\ (1) for that).

*${HOME}/.VideoDL.conf*
   Alternate per user configuration file.

*./VideoDL.conf*
   Current directory configuration file.

All files, if they exist, will be read in the above order. Any
conflicting keys are taken from the more recent configuration while the
previously existing keys are retained.
Therefore, if a wide variety of possible jobs are to be specified,
it is recommended to keep to a minimum
the number of config keys in the special 'DEFAULT' section
as they will cascade down the default configuration file order
into all config sections unless a section specifically overrides them.

EXAMPLE
=======

::

   [DEFAULT]
   # Change BaseDir to wherever you store your videos
   BaseDir = /home/user/Videos/AutoYTDL/Archivist
   # Both [Archivist] and [Recent] read from the same Source
   Source = ${BaseDir}/Archivist.Source.txt
   OptionsFile = ${BaseDir}/options.json
   DateSpan = today-30days

   [Archivist]
   SubDir = ${BaseDir}/Archivist
   # Grab content older than 30 days old
   DateEnd = ${DateSpan}

   [Recent]
   SubDir = ${BaseDir}/Recent
   # Grab content newer than 30 days old
   DateStart = ${DateSpan}

The above example file contains two jobs in two sections
with *job-identifier*s 'Archivist' and 'Recent'.
Those two sections inherit all values from the special 'DEFAULT' section
(they can override inherited values if needed, but that is not shown in
this example).
Also, numerous places contain the format string '${BaseDir}'
which refers to the value of the **BaseDir** config key
from the section it's in
(or, as in this case, the default value from the section 'DEFAULT').
The format string '${BaseDir}' will be expanded to its config value,
avoiding repetition of the base pathname.

SEE ALSO
========

**video-dl**\ (1), **yt-dlp**\ (1)
