.. This is an alternate manual for users without the ability to open the
   gzipped troff manuals.

This is the plain-text manual for VideoDL.
The command-line script is called ``video-dl``,
and the associated configuration file format is called VideoDL.conf.

USAGE
=====

The script loads an INI-style configuration file containing all the
information it needs to manage the download. The script’s positional
arguments, your job identifiers, specify which config sections are to be
executed.

The script will search for configuration files in the following places:

**Windows:**

-  ``%APPDATA%\VideoDL\*``
-  ``%USERPROFILE%\VideoDL\*``
-  ``%USERPROFILE%\VideoDL.conf``

**POSIX:**

-  ``/etc/VideoDL.conf``
-  ``${XDG_CONFIG_HOME}/VideoDL/*``
-  ``${HOME}/.config/VideoDL/*``
-  ``${HOME}/.VideoDL.conf``

If the argument to ``--config`` is an absolute path, the script will go
straight to that file. Otherwise it will search for the argument in the
locations signified by ``*`` above, or, if no argument, for the default
configuration file, ``default.conf``. In addition, the script will
search the current directory for the argument to ``--config`` or a file
named ``VideoDL.conf``.

Command-line arguments
----------------------

.. include:: include/SYNOPSIS.rst

Will perform the download job specified in the *job-identifier* section of
the loaded configuration.
If *job-identifier* is omitted, it performs all jobs in all sections.
A job that fails or cannot be successfully performed
will be skipped and the next tried.

Optional arguments
^^^^^^^^^^^^^^^^^^

.. include:: include/OPTIONS.rst

CONFIG FORMAT
=============

See ``examples/VideoDL.conf`` for an example configuration file,
and see ``examples/options.json`` for an example options file
(**OptionsFile**, below).

.. include:: include/CONFIGKEYS.rst
