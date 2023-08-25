#!/usr/bin/python3
#
"""Video download manager for yt-dlp"""


import argparse
import collections
import configparser
import fnmatch
import functools
import json
import logging
import os
import random
import sys
import threading
import time

import yt_dlp
from yt_dlp import optparse

try:
    import yaml
except ImportError as err:
    YAML_ERROR = err
else:
    YAML_ERROR = None
    try:
        yaml.Loader = yaml.CLoader
    except AttributeError:
        pass

__prog__ = "VideoDL"
__version__ = "0.8.0"


class ProgramLogger(logging.LoggerAdapter):
    """A LoggerAdapter that prepends the section name to the log message"""

    def process(self, msg, kwargs):
        return f"{self.extra['section']}: {msg}", kwargs


class Program:
    """Extract parameters from `section` of `config`.

    Methods generally handle the usual exceptions, logging the exception and
    returning None.
    """
    console_fmt = "%(module)s: %(levelname)s: %(message)s"
    file_fmt = "%(asctime)s %(levelno)s %(message)s"

    def __init__(self, config, section):
        self.section = section
        self.map = config[section]
        self.logger = ProgramLogger(
            logging.getLogger(__prog__), {"section": section})
        self.error = None

    def download(self, url_list, options=None):
        """Download list of URLs."""
        self.logger.debug("video queue: %s", url_list)
        with yt_dlp.YoutubeDL(options or {}) as ydl:
            self.logger.info("starting download")
            self.logger.debug(ydl.params)
            error_code = ydl.download(url_list)
        if error_code:
            self.logger.error("some videos failed to download")

    def path_is_writable(self, key):
        """For value of config key, test if value is writable path.

        Note this is a convenience not a security feature.

        Returns: path value if writable; False if not writable; None if key
          not found
        """
        w_path = self.get_required(key)
        if not w_path:
            return None
        if os.access(w_path, os.W_OK):
            return w_path
        return False

    def read_source(self, source="Source"):
        """For value of config key `source`, read list file.

        Returns: list of lines in file (ignoring comments); None if key not
          found or file not readable
        """
        s_path = self.get_required(source)
        if not s_path:
            return None
        try:
            s_file = open(s_path, "r", encoding="utf-8", errors="ignore")
        except OSError:
            self.logger.exception("can't read source file %s", s_path)
            return None
        with s_file:
            self.logger.debug("reading batch urls from '%s'", s_path)
            return yt_dlp.utils.read_batch_urls(s_file)

    def shuffle_source(self, url_list, key="ShuffleSource"):
        if self.get_boolean(key):
            self.logger.debug("shuffling video queue")
            random.shuffle(url_list)

    def read_options(self, options="OptionsFile", interpret=False):
        """For value of config key `options`, read options from JSON or YAML.

        Returns: dictionary of options from JSON (or YAML) file or empty
          dictionary if key not found; None if file cannot be located or read
        """
        o_path = self.map.get(options)
        if not o_path:
            # No OptionsFile specified or empty value
            return {}
        load = json.load
        file_is_yaml = any(fnmatch.fnmatch(o_path, pattern)
                           for pattern in frozenset({"*.yaml", "*.yml"}))
        if file_is_yaml:
            if YAML_ERROR:
                self.logger.warning(
                    "YAML file %s given, but PyYAML is not installed", o_path)
                # Try parsing as JSON anyway
            else:
                load = functools.partial(yaml.load, Loader=yaml.Loader)
        try:
            o_file = open(o_path, "r", encoding="utf-8")
        except OSError:
            self.logger.exception("can't read options file %s", o_path)
            return None
        with o_file:
            try:
                options = load(o_file)
            except (json.JSONDecodeError, yaml.YAMLError):
                self.logger.exception("unable to parse options file %s",
                                      o_path)
                return None
        if interpret:
            try:
                return self.interpret_options(options)
            except optparse.OptParseError:
                self.logger.exception("error parsing options array")
                return None
        return options

    def interpret_options(self, options):
        """Parse argument vector in `options` as command-line options.

        Interpret value of ``VideoDL://options`` as an array of command-line
        options. Postprocessors are appended to the existing list of
        postprocessors. All other keys are merged in a ChainMap.
        """
        opt_key = "VideoDL://options"
        if array := options.get(opt_key):
            if not isinstance(array, list):
                self.logger.warning("found key %s, but value is not an array",
                                    opt_key)
                return options
            parsed = cli_to_api(array)
            self.logger.debug("parsed options %s", parsed)
            if "postprocessors" in parsed:
                options.setdefault("postprocessors", [])
                options["postprocessors"].extend(parsed["postprocessors"])
            return collections.ChainMap(options, parsed)
        return options

    def get_date_range(self, start="DateStart", end="DateEnd"):
        """For values of config keys, convert to single DateRange object."""
        start_val = self.map.get(start)
        end_val = self.map.get(end)
        return MyDateRange(start=start_val, end=end_val)

    def get_output_logger(self, key="Log", console_level=logging.INFO):
        """Configure and return logger for yt_dlp."""
        log_path = self.map.get(key)
        # Not to be confused with self.logger which is the module logger
        logger = logging.getLogger(name=self.section)
        logger.setLevel(logging.DEBUG)
        if self.distinguish_debug():
            logger.debug = promote_info_logs(logger.debug)
        console_hdlr = logging.StreamHandler()
        console_hdlr.setLevel(console_level)
        console_hdlr.setFormatter(logging.Formatter(self.console_fmt))
        logger.addHandler(console_hdlr)
        if log_path:
            file_hdlr = logging.FileHandler(
                log_path, mode=self.parse_log_mode())
            file_hdlr.setLevel(logging.DEBUG)
            file_hdlr.setFormatter(self.get_output_logger_formatter())
            logger.addHandler(file_hdlr)
        return logger

    def distinguish_debug(self, key="DistinguishDebug"):
        return self.get_boolean(key, False)

    def get_output_logger_formatter(self,
                                    fmt_key="LogFmt",
                                    datefmt_key="LogDateFmt"):
        fmt = self.map.get(fmt_key, self.file_fmt)
        datefmt = self.map.get(datefmt_key)
        return logging.Formatter(fmt=fmt, datefmt=datefmt)

    def parse_log_mode(self, key="LogMode"):
        log_mode = self.map.get(key, "").lower()
        if log_mode in frozenset({"a", "append"}):
            return "a"
        if log_mode in frozenset({"w", "overwrite", "truncate"}):
            return "w"
        if log_mode:
            self.logger.warning(
                "unrecognized LogMode %r, defaulting to Overwrite", log_mode)
        return "w"

    def get_required(self, key):
        try:
            return self.map[key]
        except KeyError:
            self.logger.exception("required key %r not found in section", key)
            return None

    def get_boolean(self, key, default=False):
        try:
            return self.map.getboolean(key, default)
        except ValueError:
            self.logger.warning(
                "unrecognized boolean value for %s: '%s' (defaulting to %s)",
                key, self.map.get(key), default)
        return default

    def progress_hook(self, progress_info):
        if progress_info["status"] == "error":
            self.logger.error("error with job")
            self.logger.debug(progress_info["info_dict"])
            self.error = True
        if progress_info["status"] == "finished":
            self.logger.info("Done downloading, now converting: %s",
                progress_info["info_dict"].get("title", "<no title>"))
            self.logger.debug(
                "final filename: '%s', tmpfilename: '%s', "
                "downloaded_bytes: %d, seconds elapsed: %d",
                progress_info.get("filename"),
                progress_info.get("tmpfilename"),
                progress_info.get("downloaded_bytes"),
                progress_info.get("elapsed"))

    def parse_interval_random(self, key):
        """
        Parse value of config key as an interval, and return a random number
        in that interval.

        The value should consist of either one argument or two comma-separated
        arguments. Arguments should be parsable by `duration`. If one argument,
        the interval is [0, arg]. Otherwise the result is bounded by the two
        arguments.

        If the value is missing or cannot be parsed, return 0.0.
        """
        value = self.map.get(key)
        if not value:
            return 0.0
        try:
            argv = iter([duration(arg) for arg in value.split(',')])
        except ValueError:
            self.logger.warning("invalid argument to %s: %s", key, value)
            return 0.0
        upper = next(argv, 0.0)
        lower = next(argv, 0.0)
        return random.uniform(lower, upper)

    def random_sleep(self, key="SleepInterval"):
        """
        Parse value of config key, and sleep for a random duration in that
        interval (as parsed by `parse_interval_random`).

        Returns: number of seconds slept for
        """
        interval = self.parse_interval_random(key)
        if interval <= 0.0:
            return 0.0
        self.logger.info("sleeping for %s before starting",
                         format_duration(interval))
        time.sleep(interval)
        return interval


class MyDateRange(yt_dlp.utils.DateRange):
    """Represents a time interval between two dates

    >>> MyDateRange(start="20050403")
    MyDateRange(start='20050403', end='99991231')
    """

    def __repr__(self):
        # Turn self.start and self.end back into canonical string format
        date_fmt = "%Y%m%d"
        # glibc represents year 1 as '1', while (all?) other C libraries
        # represent it as '0001', hence str.zfill for cross-platform
        # consistency. See issue32195.
        start_str = self.start.strftime(date_fmt).zfill(8)
        return (f"{type(self).__name__}("
                f"start='{start_str}', end='{self.end:{date_fmt}}')")


def main():
    args = parse_cla()
    config = search_configs(args.config)
    if not config:
        logger = get_logger()
        logger.error("unable to find configuration file")
        return 100
    logger = get_logger(**get_logger_options(config),
                        console_level=args.log_level)
    logger.debug("config file(s): %s", config.get("DEFAULT", "PATHS"))
    logger.debug("%s version %s", __prog__, __version__)

    if args.sleep:
        interval = random.uniform(0.0, args.sleep)
        logger.info("sleeping for %s before starting",
                    format_duration(interval))
        time.sleep(interval)

    clock_start = time.perf_counter()
    for job in args.job_identifier or config.sections():
        if not config.has_section(job):
            logger.error("no config section found with name %r", job)
            continue
        prog = Program(config=config, section=job)
        subdir = prog.path_is_writable(key="SubDir")
        if not subdir:
            logger.warning("path is not writable: %s, skipping %s",
                           subdir, job)
            continue
        if not os.path.isdir(subdir):
            logger.warning("path is not a directory: %s, skipping %s",
                           subdir, job)
            continue
        url_list = prog.read_source()
        if url_list is None:
            logger.warning("unable to read source file, skipping %s", job)
            continue
        prog.shuffle_source(url_list)
        ydl_opts = prog.read_options(interpret=True)
        if ydl_opts is None:
            logger.warning("unable to read options file, skipping %s", job)
            continue
        ydl_opts["download_archive"] = prog.map.get("DownloadArchive")
        ydl_opts["logger"] = prog.get_output_logger(
            console_level=args.log_level)
        ydl_opts["daterange"] = prog.get_date_range()
        ydl_opts["progress_hooks"] = [prog.progress_hook]
        # Make outtmpl absolute
        outtmpl = ydl_opts.get("outtmpl")
        ydl_opts["outtmpl"] = os.path.join(
            subdir, outtmpl or yt_dlp.utils.DEFAULT_OUTTMPL["default"])
        clock_start += prog.random_sleep()
        prog.download(url_list, ydl_opts)
    clock_stop = time.perf_counter()
    logger.info("finished all jobs in %s",
                format_duration(clock_stop - clock_start))
    return 0


def cli_to_api(opts):
    """Return a dictionary of options parsed from `opts`.

    Only options with values different from the defaults will be included.

    >>> cli_to_api([])
    {}
    >>> cli_to_api(["--concurrent-fragments=2"])
    {'concurrent_fragment_downloads': 2}
    """
    def parse_options(opts):
        return yt_dlp.parse_options(opts).ydl_opts
    default_opts = parse_options([])
    opts = parse_options(opts)
    diff = {key: val for key, val in opts.items()
            if default_opts[key] != val}
    if "postprocessors" in diff:
        diff["postprocessors"] = [pp for pp in diff["postprocessors"]
                                  if pp not in default_opts["postprocessors"]]
    return diff


def promote_info_logs(std_debug):
    """
    Return a logging.Logger.debug method that distinguishes debug by the msg
    prefix '[debug] '.
    """
    @functools.wraps(std_debug)
    def wrapper(msg, *args, **kwargs):
        if msg.startswith("[debug] "):
            return std_debug(msg, *args, **kwargs)
        return std_debug.__self__.info(msg, *args, **kwargs)
    return wrapper


def get_logger_options(config):
    opts = {}
    opts["file"] = config.get("DEFAULT", "MasterLog", fallback=None)
    opts["file_level"] = parse_log_level(config.get(
        "DEFAULT", "MasterLogLevel", fallback=""))
    opts["file_fmt"] = config.get("DEFAULT", "MasterLogFmt", fallback=None)
    opts["file_datefmt"] = config.get(
        "DEFAULT", "MasterLogDateFmt", fallback=None)
    return opts


def search_configs(config_path=None):
    """Read config file at config_path else search."""
    config = configparser.ConfigParser(
        interpolation=configparser.ExtendedInterpolation())
    if config_path and os.path.isabs(config_path):
        # absolute path given -- read one only
        paths = config.read(config_path)
    else:
        paths = config.read(search_nearby_files(config_path))
    if not paths:
        return None
    # Include in config list of filenames which were successfully parsed
    config.set("DEFAULT", "PATHS", str(paths))
    return config


def search_nearby_files(basename=None):
    r"""Search for configuration files in the following places.

    Windows:
        - %APPDATA%\VideoDL\*
        - %USERPROFILE%\VideoDL\*
        - %USERPROFILE%\VideoDL.conf

    POSIX:
        - /etc/VideoDL.conf
        - ${XDG_CONFIG_HOME}/VideoDL/*
        - ${HOME}/.config/VideoDL/*
        - ${HOME}/.VideoDL.conf

    All:
        - current directory
    """
    standalone = __prog__ + ".conf"
    select = basename or "default.conf"
    if os.name == "nt":
        if (appdata := os.getenv("APPDATA")):
            yield os.path.join(appdata, __prog__, select)
        if (userprofile := os.getenv("USERPROFILE")):
            yield os.path.join(userprofile, __prog__, select)
            yield os.path.join(userprofile, standalone)
    elif os.name == "posix":
        yield os.path.join("etc", standalone)
        if (xdg_config_home := os.getenv("XDG_CONFIG_HOME")):
            yield os.path.join(xdg_config_home, __prog__, select)
        if (home := os.getenv("HOME")):
            yield os.path.join(home, ".config", __prog__, select)
            yield os.path.join(home, "." + standalone)
    if basename:
        yield os.path.join(".", basename)
    yield os.path.join(".", standalone)


def get_logger(file=None,
               console_level=logging.INFO,
               file_level=logging.DEBUG,
               file_fmt=None,
               file_datefmt=None):
    """Configure and return module logger."""
    logger = logging.getLogger(__prog__)
    logger.setLevel(logging.DEBUG)
    console_hdlr = logging.StreamHandler()
    console_hdlr.setLevel(console_level)
    console_hdlr.setFormatter(logging.Formatter(Program.console_fmt))
    logger.addHandler(console_hdlr)
    if file:
        file_hdlr = logging.FileHandler(file)
        file_hdlr.setLevel(file_level)
        legacy_fmt = "%(asctime)s *** %(levelname)s %(message)s"
        fmt = file_fmt if file_fmt is not None else legacy_fmt
        iso_8601_sec = "%Y-%m-%dT%H:%M:%S%z"
        datefmt = file_datefmt if file_datefmt is not None else iso_8601_sec
        file_hdlr.setFormatter(
            logging.Formatter(fmt=fmt, datefmt=datefmt))
        logger.addHandler(file_hdlr)
    return logger


def parse_log_level(string):
    """Parse log level value from config.

    Accept a string containing either a standard log level name ("DEBUG",
    "INFO", etc.) or some decimal integer. An invalid string returns default
    value of logging.DEBUG (10).
    """
    level = getattr(logging, string.upper(), string)
    try:
        return int(level)
    except ValueError:
        return logging.DEBUG


def parse_cla():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser()
    parser.add_argument("-V", "--version", action="version",
                        version=f"%(prog)s {__version__}")
    parser.add_argument("job_identifier", nargs="*", metavar="job-identifier",
                        help="section in configuration to read "
                             "(default is all sections)")
    parser.add_argument("-C", "--config", metavar="FILE",
                        type=os.path.expanduser,
                        help="load configuration from %(metavar)s")
    verbosity = parser.add_mutually_exclusive_group()
    verbosity.add_argument("-d", "--debug", action="store_const",
                           const=logging.DEBUG, default=logging.INFO,
                           dest="log_level",
                           help="print debug information")
    verbosity.add_argument("-q", "--quiet", action="store_const",
                           const=logging.WARNING, default=logging.INFO,
                           dest="log_level",
                           help="don't print info messages")
    parser.add_argument("-s", "--sleep", type=duration, metavar="SEC",
                        help="sleep for a random duration between 0 and "
                             "%(metavar)s seconds before starting")
    return parser.parse_args()


def duration(seconds):
    """Convert a string representing a decimal, positive, real number."""
    dur = float(seconds)
    if 0.0 <= dur <= threading.TIMEOUT_MAX:
        return dur
    raise ValueError


def format_duration(seconds):
    t_min, t_sec = divmod(seconds, 60.0)
    if t_min <= 0.0:
        return f"{t_sec:.1f}s"
    return f"{t_min:.0f}m{t_sec:.0f}s"


if __name__ == "__main__":
    sys.exit(main())
