#!/usr/bin/python3
#
"""Video download manager for yt-dlp"""

from __future__ import annotations

import argparse
import collections
import configparser
import dataclasses
import fnmatch
import functools
import json
import logging
import os
import random
import sys
import threading
import time
import types
from collections.abc import Callable, Iterator, Mapping, MutableMapping
from pathlib import Path
from typing import Any, NamedTuple, NoReturn, TypeVar

import yt_dlp  # type: ignore

try:
    import yaml as _yaml
except ImportError:
    _HAS_YAML = False
else:
    _HAS_YAML = True

__version__ = "1.0.1"
PROG = "VideoDL"
CONSOLE_FMT = "%(module)s: %(levelname)s: %(message)s"
LEGACY_LOG_FMT = "%(asctime)s *** %(levelname)s %(message)s"
ISO_8601_SEC = "%Y-%m-%dT%H:%M:%S%z"

D = TypeVar("D", bound="Duration")
MM = TypeVar("MM", bound="MutableMapping")


class Duration(float):
    """A duration of seconds"""

    @classmethod
    def parse_string(cls: type[D], seconds: str) -> D:
        """Convert a string representing a decimal, positive, real number."""
        dur = float(seconds)
        if not 0.0 <= dur <= threading.TIMEOUT_MAX:
            msg = f"duration negative or too large: {dur!r}"
            raise ValueError(msg)
        return cls(dur)

    def format(self) -> str:
        """Return formatted duration string.

        >>> Duration(500).format()
        '8m20s'
        """
        if self <= Duration(60.0):
            return f"{self:.1f}s"
        t_min, t_sec = divmod(round(self), 60)
        return f"{t_min}m{t_sec}s"

    def __repr__(self) -> str:
        return f"{type(self).__name__}({super().__repr__()})"


@dataclasses.dataclass
class TimeInterval:
    lower: Duration = Duration(0.0)
    upper: Duration = Duration(0.0)

    def random_duration(self) -> Duration:
        return Duration(random.uniform(self.lower, self.upper))


class Job:
    def __init__(
        self,
        urls: list[str],
        options: MutableMapping[str, Any] | None = None,
        sleep_interval: TimeInterval | tuple[float, float] | None = None,
        logger: logging.Logger | logging.LoggerAdapter | None = None,
    ) -> None:
        self.urls = urls
        self.options = options if options is not None else {}
        self.options["progress_hooks"] = [self.progress_hook]
        if sleep_interval is None:
            self.sleep_interval = TimeInterval()
        elif isinstance(sleep_interval, TimeInterval):
            self.sleep_interval = sleep_interval
        else:
            self.sleep_interval = TimeInterval(*map(Duration, sleep_interval))
        self.logger = logger or logging.getLogger(PROG)

    def random_sleep(self) -> Duration:
        period = self.sleep_interval.random_duration()
        if period <= 0.0:
            return Duration(0.0)
        self.logger.info("sleeping for %s before starting", period.format())
        time.sleep(period)
        return period

    def download(self) -> None:
        self.logger.debug("video queue: %s", self.urls)
        with yt_dlp.YoutubeDL(self.options) as ydl:
            self.logger.info("starting download")
            self.logger.debug(ydl.params)
            error_code = ydl.download(self.urls)
        if error_code:
            self.logger.error("some videos failed to download")

    def progress_hook(self, progress_info: Mapping) -> None:
        if progress_info["status"] == "error":
            self.logger.error("error with job")
            self.logger.debug(progress_info["info_dict"])
        if progress_info["status"] == "finished":
            self.logger.info(
                "Done downloading, now converting: %s",
                progress_info["info_dict"].get("title", "<no title>"),
            )
            self.logger.debug(
                "final filename: '%s', tmpfilename: '%s', "
                "downloaded_bytes: %d, seconds elapsed: %d",
                progress_info.get("filename"),
                progress_info.get("tmpfilename"),
                progress_info.get("downloaded_bytes"),
                progress_info.get("elapsed"),
            )


class ProgramLogger(logging.LoggerAdapter):
    """A LoggerAdapter that prepends the section name to the log message"""

    def process(self, msg, kwargs):
        return f"{self.extra['section']}: {msg}", kwargs


class Program:
    """Extract parameters from *section* of *config*.

    Methods generally handle the usual exceptions, logging the exception and
    returning None.
    """

    FILE_FMT = "%(asctime)s %(levelno)s %(message)s"

    def __init__(self, config: configparser.ConfigParser, section: str) -> None:
        self.section = section
        self.map = config[section]
        self.logger = ProgramLogger(logging.getLogger(PROG), {"section": section})

    def read_source(self, key: str = "Source") -> list[str] | None:
        s_path = self.get_required(key=key)
        if not s_path:
            return None
        try:
            s_file = open(s_path, "r", encoding="utf-8", errors="ignore")
        except OSError as err:
            self.logger.exception("can't read source file: %s", err)
            return None
        with s_file:
            self.logger.debug("reading batch urls from '%s'", s_path)
            return yt_dlp.utils.read_batch_urls(s_file)

    def shuffle_source(self, urls: list[str], key: str = "ShuffleSource") -> None:
        if self.get_boolean(key):
            self.logger.debug("shuffling video queue")
            random.shuffle(urls)

    def read_options(
        self, key: str = "OptionsFile", interpret: bool = False
    ) -> dict | collections.ChainMap | None:
        o_path = self.map.get(key)
        if not o_path:
            return {}
        load = self._load_json
        file_is_yaml = any(
            fnmatch.fnmatch(o_path, pattern) for pattern in ("*.yaml", "*.yml")
        )
        if file_is_yaml:
            if not _HAS_YAML:
                self.logger.warning(
                    "YAML file %s given, but PyYAML is not installed", o_path
                )
            # Try parsing as JSON anyway
            else:
                load = self._load_yaml
        try:
            o_file = open(o_path, "r", encoding="utf-8")
        except OSError as err:
            self.logger.exception("can't read options file: %s", err)
            return None
        with o_file:
            options = load(o_file)
        if options is None:
            self.logger.error("unable to parse options file: %s", o_path)
            return None
        if interpret:
            try:
                return self.interpret_options(options)
            except yt_dlp.optparse.OptParseError:
                self.logger.exception("error parsing options array")
                return None
        return options

    @staticmethod
    def _load_json(o_file) -> Any | None:
        try:
            return json.load(o_file)
        except json.JSONDecodeError:
            return None

    @staticmethod
    def _load_yaml(o_file) -> Any | None:
        loader = getattr(_yaml, "CLoader", _yaml.Loader)
        try:
            return _yaml.load(o_file, Loader=loader)
        except _yaml.YAMLError:
            return None

    def interpret_options(self, options: MM) -> MM | collections.ChainMap:
        """Parse argument vector in *options* as command-line options.

        Interpret value of ``VideoDL://options`` as an array of command-line
        options. Postprocessors are appended to the existing list of
        postprocessors. All other keys are merged in a ChainMap.
        """
        opt_key = "VideoDL://options"
        if array := options.get(opt_key):
            if not isinstance(array, list):
                self.logger.warning("found key %s, but value is not an array", opt_key)
                return options
            parsed = cli_to_api(array)
            self.logger.debug("parsed options %s", parsed)
            if "postprocessors" in parsed:
                options.setdefault("postprocessors", [])
                options["postprocessors"].extend(parsed["postprocessors"])
            return collections.ChainMap(options, parsed)
        return options

    def get_date_range(
        self, start_key: str = "DateStart", end_key: str = "DateEnd"
    ) -> MyDateRange:
        """For values of config keys, convert to single DateRange object."""
        start_val = self.map.get(start_key)
        end_val = self.map.get(end_key)
        return MyDateRange(start=start_val, end=end_val)

    def get_output_logger(
        self, key: str = "Log", console_level: int = logging.INFO
    ) -> logging.Logger:
        """Configure and return logger for yt_dlp."""
        # Not to be confused with self.logger which is the module logger
        logger = logging.getLogger(name=self.section)
        logger.setLevel(logging.DEBUG)
        if self.distinguish_debug():
            # Avoid mypy error "can't assign to a method". This is a limitation
            # of mypy (issue #708).
            logger.debug = promote_info_logs(logger.debug)  # type: ignore
        console_hdlr = logging.StreamHandler()
        console_hdlr.setLevel(console_level)
        console_hdlr.setFormatter(logging.Formatter(CONSOLE_FMT))
        logger.addHandler(console_hdlr)
        if log_path := self.map.get(key):
            file_hdlr = logging.FileHandler(log_path, mode=self.parse_log_mode())
            file_hdlr.setLevel(logging.DEBUG)
            file_hdlr.setFormatter(self.get_output_logger_formatter())
            logger.addHandler(file_hdlr)
        return logger

    def distinguish_debug(self, key: str = "DistinguishDebug") -> bool:
        return self.get_boolean(key, False)

    def get_output_logger_formatter(
        self, fmt_key: str = "LogFmt", datefmt_key: str = "LogDateFmt"
    ) -> logging.Formatter:
        fmt = self.map.get(fmt_key, self.FILE_FMT)
        datefmt = self.map.get(datefmt_key)
        return logging.Formatter(fmt=fmt, datefmt=datefmt)

    def parse_log_mode(self, key: str = "LogMode") -> str:
        log_mode = self.map.get(key, "").lower()
        if log_mode in {"a", "append"}:
            return "a"
        if log_mode in {"w", "overwrite", "truncate"}:
            return "w"
        if log_mode:
            self.logger.warning(
                "unrecognized LogMode %r, defaulting to Overwrite", log_mode
            )
        return "w"

    def get_required(self, key: str) -> str | None:
        try:
            return self.map[key]
        except KeyError:
            self.logger.exception("required key not found in section: %s", key)
            return None

    def get_boolean(self, key: str, default: bool = False) -> bool:
        try:
            return self.map.getboolean(key, default)
        except ValueError:
            self.logger.warning(
                "unrecognized boolean value for %s: '%s' (defaulting to %s)",
                key,
                self.map.get(key),
                default,
            )
        return default

    def parse_interval(self, key: str = "SleepInterval") -> TimeInterval:
        value = self.map.get(key)
        if not value:
            return TimeInterval()
        try:
            argv = iter([Duration.parse_string(arg) for arg in value.split(",")])
        except ValueError:
            self.logger.warning("invalid argument to %s: %s", key, value)
            return TimeInterval()
        lower = next(argv, Duration(0.0))
        upper = next(argv, Duration(0.0))
        return TimeInterval(lower=lower, upper=upper)


class MyDateRange(yt_dlp.utils.DateRange):
    """Represents a time interval between two dates

    >>> MyDateRange(start="20050403")
    MyDateRange(start='20050403', end='99991231')
    """

    def __repr__(self) -> str:
        # Turn self.start and self.end back into canonical string format
        date_fmt = "%Y%m%d"
        # glibc represents year 1 as '1', while (all?) other C libraries
        # represent it as '0001', hence str.zfill for cross-platform
        # consistency. See issue32195.
        start_str = self.start.strftime(date_fmt).zfill(8)
        return (
            f"{type(self).__name__}("
            f"start='{start_str}', end='{self.end:{date_fmt}}')"
        )


class Config(NamedTuple):
    parser: configparser.ConfigParser
    files_read: list[str] | None = None


# pylint: disable=too-few-public-methods
class Args(types.SimpleNamespace):
    job_identifier: list[str]
    config: str | None
    log_level: int
    sleep: Duration | None


def main() -> None:
    args = parse_cla()
    init_logging(args.log_level)
    try:
        config = search_configs(args.config)
    except configparser.Error as err:
        die(100, "error with configuration file: %s", err)
    if not config.files_read:
        die(100, "unable to find configuration file")
    setup_file_logging(config.parser)
    logger = logging.getLogger(PROG)
    logger.debug("config file(s): %s", config.files_read)
    logger.debug("%s version %s", PROG, __version__)

    clock_start = time.perf_counter()
    try:
        jobs = list(parse_config(config.parser, args.job_identifier, args.log_level))
    except configparser.Error as err:
        die(100, "error with configuration file: %s", err)
    logger.debug("%d job(s) queued", len(jobs))
    if jobs and args.sleep:
        period = TimeInterval(Duration(0.0), args.sleep).random_duration()
        logger.info("sleeping for %s before starting", period.format())
        time.sleep(period)
        clock_start += period
    for job in jobs:
        clock_start += job.random_sleep()
        job.download()
    clock_stop = time.perf_counter()
    logger.info("finished all jobs in %s", Duration(clock_stop - clock_start).format())


def parse_config(
    config: configparser.ConfigParser,
    job_identifiers: list[str] | None = None,
    console_level: int = logging.INFO,
) -> Iterator[Job]:
    logger = logging.getLogger(PROG)

    for job in job_identifiers or config.sections():
        if not config.has_section(job):
            logger.error("no config section found with name: %s", job)
            continue
        prog = Program(config=config, section=job)
        subdir_val = prog.get_required(key="SubDir")
        if not subdir_val:
            continue
        subdir = Path(subdir_val)
        if not os.access(subdir, os.W_OK):
            # Note this is a convenience not a security feature.
            logger.warning("path is not writable, skipping %s: %s", job, subdir)
            continue
        if not subdir.is_dir():
            logger.warning("path is not a directory, skipping %s: %s", job, subdir)
            continue
        url_list = prog.read_source()
        if url_list is None:
            logger.warning("unable to read source file, skipping %s", job)
            continue
        ydl_opts = prog.read_options(interpret=True)
        if ydl_opts is None:
            logger.warning("unable to read options file, skipping %s", job)
            continue

        prog.shuffle_source(url_list)

        ydl_opts["download_archive"] = prog.map.get("DownloadArchive")
        ydl_opts["logger"] = prog.get_output_logger(console_level=console_level)
        ydl_opts["daterange"] = prog.get_date_range()
        ydl_opts["outtmpl"] = str(
            subdir / ydl_opts.get("outtmpl", yt_dlp.utils.DEFAULT_OUTTMPL["default"])
        )

        yield Job(url_list, ydl_opts, prog.parse_interval(), logger=prog.logger)


def die(status: int, *msg: object) -> NoReturn:
    logger = logging.getLogger(PROG)
    logger.error(*msg)
    sys.exit(status)


def cli_to_api(args: list[str]) -> dict:
    """Return a dictionary of options parsed from *args*.

    Only options with values different from the defaults will be included.

    >>> cli_to_api([])
    {}
    >>> cli_to_api(["--concurrent-fragments=2"])
    {'concurrent_fragment_downloads': 2}
    """

    def parse_options(args: list[str]) -> dict:
        return yt_dlp.parse_options(args).ydl_opts

    default_opts = parse_options([])
    opts = parse_options(args)
    diff = {key: val for key, val in opts.items() if default_opts[key] != val}
    if "postprocessors" in diff:
        diff["postprocessors"] = [
            pp
            for pp in diff["postprocessors"]
            if pp not in default_opts["postprocessors"]
        ]
    return diff


def promote_info_logs(std_debug: Callable[..., None]) -> Callable[..., None]:
    """
    Return a logging.Logger.debug method that distinguishes debug by the msg
    prefix '[debug] '.
    """

    @functools.wraps(std_debug)
    def wrapper(msg: object, *args: object, **kwargs: Any):
        # Assuming msg is a str
        try:
            debug = msg.startswith("[debug] ")  # type: ignore
        except AttributeError:
            debug = False
        if debug:
            return std_debug(msg, *args, **kwargs)
        return std_debug.__self__.info(msg, *args, **kwargs)  # type: ignore

    return wrapper


def search_configs(config_path: str | None = None) -> Config:
    """Read config file at *config_path* else search."""
    parser = configparser.ConfigParser(
        interpolation=configparser.ExtendedInterpolation()
    )
    if config_path and Path(config_path).is_absolute():
        # absolute path given -- read one only
        paths = parser.read(config_path)
    else:
        paths = parser.read(search_nearby_files(config_path))
    return Config(parser=parser, files_read=paths)


def search_nearby_files(basename: str | None = None) -> Iterator[Path]:
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
    standalone = f"{PROG}.conf"
    select = basename or "default.conf"
    if os.name == "nt":
        if appdata := os.getenv("APPDATA"):
            yield Path(appdata, PROG, select)
        if userprofile := os.getenv("USERPROFILE"):
            yield Path(userprofile, PROG, select)
            yield Path(userprofile, standalone)
    elif os.name == "posix":
        yield Path("etc", standalone)
        if xdg_config_home := os.getenv("XDG_CONFIG_HOME"):
            yield Path(xdg_config_home, PROG, select)
        if home := os.getenv("HOME"):
            yield Path(home, ".config", PROG, select)
            yield Path(home, f".{standalone}")
    if basename:
        yield Path.cwd() / basename
    yield Path.cwd() / standalone


def init_logging(console_level: int = logging.INFO) -> None:
    """Initialize the module logger with stderr logging."""
    logger = logging.getLogger(PROG)
    logger.setLevel(logging.DEBUG)
    console_hdlr = logging.StreamHandler()
    console_hdlr.setLevel(console_level)
    console_hdlr.setFormatter(logging.Formatter(CONSOLE_FMT))
    logger.addHandler(console_hdlr)


def setup_file_logging(config: configparser.ConfigParser) -> None:
    """Add file logging to the module logger."""
    settings = config[config.default_section]
    logger = logging.getLogger(PROG)
    if file := settings.get("MasterLog"):
        try:
            file_hdlr = logging.FileHandler(file)
        except OSError as err:
            logger.error("unable to open MasterLog for writing: %s", err)
            return
        if file_level := settings.get("MasterLogLevel"):
            file_hdlr.setLevel(parse_log_level(file_level))
        else:
            file_hdlr.setLevel(logging.DEBUG)
        fmt = settings.get("MasterLogFmt", LEGACY_LOG_FMT)
        datefmt = settings.get("MasterLogDateFmt", ISO_8601_SEC)
        file_hdlr.setFormatter(logging.Formatter(fmt=fmt, datefmt=datefmt))
        logger.addHandler(file_hdlr)


def parse_log_level(string: str) -> int:
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


def parse_cla() -> Args:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-V", "--version", action="version", version=f"%(prog)s {__version__}"
    )
    parser.add_argument(
        "job_identifier",
        nargs="*",
        metavar="job-identifier",
        help="section in configuration to read (default is all sections)",
    )
    parser.add_argument(
        "-C", "--config", metavar="FILE", help="load configuration from %(metavar)s"
    )
    verbosity = parser.add_mutually_exclusive_group()
    verbosity.add_argument(
        "-d",
        "--debug",
        action="store_const",
        const=logging.DEBUG,
        default=logging.INFO,
        dest="log_level",
        help="print debug information",
    )
    verbosity.add_argument(
        "-q",
        "--quiet",
        action="store_const",
        const=logging.WARNING,
        default=logging.INFO,
        dest="log_level",
        help="don't print info messages",
    )
    parser.add_argument(
        "-s",
        "--sleep",
        type=Duration.parse_string,
        metavar="SEC",
        help="sleep for a random duration between 0 and %(metavar)s seconds before starting",
    )
    return parser.parse_args(namespace=Args())


if __name__ == "__main__":
    main()
