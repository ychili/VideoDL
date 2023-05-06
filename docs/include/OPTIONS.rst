**-h**, **--help**
   Display the help message.

**-V**, **--version**
   Display the version number.

**-c** *FILE*, **--config=**\ *FILE*
   Configuration file.
   If *FILE* is an absolute path,
   the script will go straight to that file.
   Otherwise it will search for *FILE* in the
   per user configuration file directory (see FILES section below)
   and in the current directory.
   If this option is omitted,
   the default configuration files are read (see below).

**-d**, **--debug**
   Print debug information.
   Most of the usual messages emitted by the YTDL downloader count as
   debug messages,
   unless the **DistinguishDebug** configuration option is set,
   whereupon most will be counted as info messages.

**-q**, **--quiet**
   Don’t print info messages.
   Only print messages of level WARNING and above.

**-s** *SEC*, **--sleep=**\ *SEC*
   Sleep for a random duration between 0 and *SEC* seconds before starting.
