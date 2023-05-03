Required keys
-------------

**SubDir =** *directory*
   Videos will be downloaded to *directory*. The "outtmpl" (output
   template) that you specify in your options JSON will be computed
   relative to this.

**Source =** *file*
   *file* is a batch file with urls to read. Same format as YTDL batch
   file: one URL per line, comment lines starting with '#' ignored.

Optional keys
-------------

**OptionsFile =** *file*
   *file* is a file in JSON format containing options to pass to YTDL.
   If you have `PyYAML <https://pyyaml.org/>`__ installed, you can use a
   YAML formatted file instead of JSON. The decoded JSON object will be
   passed to the ``yt_dlp.YoutubeDL`` class constructor. Consult the
   documentation for the ``yt_dlp.YoutubeDL`` class constructor for a
   full description of available options.

**MasterLog =** *file*
   Write log messages produced by **video-dl**\ (1) to *file*. Must be
   in DEFAULT section of config. This is where, for example, the message
   that a particular section failed and was skipped will be logged.

**MasterLogLevel =** {DEBUG, INFO, WARNING, ERROR, CRITICAL}
   The log level for **MasterLog**. Can be a named log level like
   'DEBUG' or a numeric level. Defaults to DEBUG. Must be in DEFAULT
   section of config.

**MasterLogFmt =** *fmt*
   The log format for **MasterLog**. See section on "Log formatting".
   The default *fmt* is ``%(asctime)s *** %(levelname)s %(message)s``.

**MasterLogDateFmt =** *datefmt*
   The date format for **MasterLog**. This is the format that the
   ``asctime`` attribute uses. The default *datefmt* is
   '%Y-%m-%dT%H:%M:%S%z', the same format as GNU
   ``date --iso-8601=seconds`` (example: 2006-08-14T02:34:56-06:00).

**Log =** *file*
   Write downloader messages to *file.* This log file was originally
   separated from **MasterLog** so that downloader messages could be
   logged to the same external drive as the videos were downloaded to,
   while error messages relating to the execution of the download job
   itself (such as a disconnected external drive) could be logged to an
   internal drive.

**LogMode =** {append, overwrite}
   Default behavior is to overwrite the downloader output log each time
   it is opened ('overwrite' or 'truncate'). Set this to 'append' to
   append to the existing log file instead.

**LogFmt =** *fmt*
   The log format for **Log**. See section on "Log formatting". The
   default *fmt* is ``%(asctime)s %(levelno)s %(message)s``.

**LogDateFmt =** *datefmt*
   The date format for **Log**. This is the format that the ``asctime``
   attribute uses. The default *datefmt* is '%Y-%m-%d %H:%M:%S,uuu', the
   default format used by Python’s ``logging.Formatter.formatTime``
   (example: 2003-01-23 00:29:50,411).

**DistinguishDebug =** *boolean*
   If set, log downloader messages at the level INFO
   unless they are specifically prefixed by '[debug]'.
   For compatibility reasons,
   YTDL logs most info messages at the level DEBUG.
   Set this option to 'on' or 'true' to distinguish real debug logs
   from other status messages.

**DownloadArchive =** *file*
   YTDL will record all the video IDs that it’s already downloaded
   to *file.*
   Optional, but highly recommended. This will prevent each program from
   downloading videos that it’s already grabbed on previous runs.

**DateStart =** *date*, **DateEnd =** *date*
   Specify the same date strings you would normally pass to
   **--date-after** and **--date-before**.
   For example, a "DateEnd: today-30days" entry
   would cause the program to ignore videos in the source list that are
   newer than 30 days old. *date* should be in the format YYYYMMDD or
   match the regular expression
   ``(now|today)[+-][0-9](day|week|month|year)(s)?``. Consult the docs
   for the function ``yt_dlp.utils.date_from_str`` for the current
   correct format.

**SleepInterval =** *maximum* [**,** *minimum*]
   Delay the execution of this job by a random amount
   of time. Takes as a value one numeric argument or two numeric
   arguments separated by a comma. If one argument, delay by a maximum
   of *maximum* seconds. If two arguments, delay by an amount between
   *maximum* and *minimum* seconds.

**ShuffleSource =** *boolean*
   If set, download URLs from **Source** in a random order.

Log formatting
--------------

The **MasterLogFmt** and **LogFmt** optional keys allow the output
format of log messages to be customized from the default. The *fmt*
string should contain log record attributes embedded as standard Python
%-style mapping keys. Consult the Python documentation’s `LogRecord
attributes <https://docs.python.org/3/library/logging.html#logrecord-attributes>`__
section for a list of available attributes.

The **MasterLogDateFmt** and **LogDateFmt** optional keys allow the
format of dates and times in log messages to be customized from the
default. Reference **strftime**\ (3) for formatting directives that can
be used in the *datefmt* string.
