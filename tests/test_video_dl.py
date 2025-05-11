import collections
import collections.abc
import configparser
import datetime
import logging
import os.path
import unittest

import video_dl

_EXPECTED_OPTIONS_FROM_EXAMPLE_FILE = {
    "verbose": True,
    "sleep_interval": 5,
    "max_sleep_interval": 30,
    "ignoreerrors": True,
    "overwrites": False,
    "continuedl": False,
    "windowsfilenames": True,
    "subtitleslangs": ["all"],
    "merge_output_format": "mkv",
}


class TestProgram(unittest.TestCase):
    def setUp(self):
        config = configparser.ConfigParser(
            interpolation=configparser.ExtendedInterpolation()
        )
        self.test_section = "SectionName"
        config.read_dict({self.test_section: {}})
        self.prog = video_dl.Program(config, self.test_section)

    def test_parse_interval(self):
        key = "TestInterval"
        # No value
        self.assertEqual(self.prog.parse_interval(key), video_dl.TimeInterval())
        # Single valid value
        self.prog.map[key] = "2"
        self.assertEqual(
            self.prog.parse_interval(key), video_dl.TimeInterval(lower=2.0)
        )
        # Single invalid value
        self.prog.map[key] = "-1"
        with self.assertLogs(level="WARNING"):
            interval = self.prog.parse_interval(key)
        self.assertEqual(interval, video_dl.TimeInterval())
        # Two valid values
        self.prog.map[key] = "3, 5"
        self.assertEqual(self.prog.parse_interval(key), video_dl.TimeInterval(3.0, 5.0))
        # All values after first two are ignored
        self.prog.map[key] = "6, 7, 15, 0"
        self.assertEqual(self.prog.parse_interval(key), video_dl.TimeInterval(6.0, 7.0))
        # One valid, one invalid
        self.prog.map[key] = "6, 8a"
        with self.assertLogs(level="WARNING"):
            interval = self.prog.parse_interval(key)
        self.assertEqual(interval, video_dl.TimeInterval())
        # No dangling commas
        self.prog.map[key] = " 3,"
        with self.assertLogs(level="WARNING"):
            interval = self.prog.parse_interval(key)
        self.assertEqual(interval, video_dl.TimeInterval())

    def test_parse_log_mode(self):
        key = "TestLogMode"
        default = "w"
        # No value
        self.assertEqual(self.prog.parse_log_mode(key), default)
        # Upper case
        self.prog.map[key] = "APPEND"
        self.assertEqual(self.prog.parse_log_mode(key), "a")
        # Unknown value
        self.prog.map[key] = "<UNKNOWN>"
        with self.assertLogs(level="WARNING"):
            mode = self.prog.parse_log_mode(key)
        self.assertEqual(mode, default)

    def test_get_boolean(self):
        key = "TestBoolean"
        default = False
        # Missing key
        self.assertEqual(self.prog.get_boolean(key, default), default)
        true_values = ("1", "on", "True", "yes")
        false_values = ("0", "off", "False", "no")
        for values, expected in (true_values, True), (false_values, False):
            for value in values:
                self.prog.map[key] = value
                self.assertEqual(self.prog.get_boolean(key, default), expected)
        invalid_values = ("2", "set", "unset")
        for value in invalid_values:
            self.prog.map[key] = value
            with self.assertLogs(level=logging.WARNING) as recording:
                self.assertEqual(self.prog.get_boolean(key, default), default)
            # Test that log message contains relevant info
            test = (
                value in msg and str(default) in msg and key in msg
                for msg in recording.output
            )
            self.assertTrue(any(test))

    def test_example_options_file(self):
        path = os.path.join(os.path.dirname(__file__), "../examples/options.json")
        key = "OptionsFile"
        self.prog.map[key] = path
        with self.assertLogs(level=logging.WARNING) as recording:
            # We want to assert that there are no warnings, so we are adding a
            # dummy warning, and then we will assert it is the only warning.
            self.prog.logger.warning("Dummy warning")
            options = self.prog.read_options(key=key, interpret=True)
        self.assertEqual(
            recording.output, ["WARNING:VideoDL:SectionName: Dummy warning"]
        )
        self.assertTrue(options)
        self.assertIsInstance(options, collections.abc.MutableMapping)
        # Check a subset of expected options.
        items_to_check = _EXPECTED_OPTIONS_FROM_EXAMPLE_FILE.items()
        for expected_key, expected_value in items_to_check:
            self.assertEqual(
                options[expected_key],
                expected_value,
                f"Value of '{expected_key}' differs.",
            )

    def test_interpret_options(self):
        opt_key = "VideoDL://options"
        options = {"key": "value", opt_key: ["--quiet", "-R", "8"]}
        with self.assertLogs(level=logging.DEBUG):
            options = self.prog.interpret_options(options)
        # But don't assume we know what values our args will be parsed into
        self.assertIsInstance(options, collections.ChainMap)
        # Original argv is unmodified
        self.assertListEqual(options[opt_key], ["--quiet", "-R", "8"])
        options[opt_key].append("--bad-option")
        with self.assertRaises(video_dl.yt_dlp.optparse.OptParseError):
            options = self.prog.interpret_options(options)


class TestDuration(unittest.TestCase):
    def test_parse_duration(self):
        dur = video_dl.Duration.parse_string
        self.assertEqual(dur("3.14"), 3.14)
        self.assertEqual(dur("3600"), 3600)
        self.assertRaises(ValueError, dur, "-1")
        self.assertRaises(ValueError, dur, "inf")

    def test_random_duration(self):
        for _ in range(4):
            dur = video_dl.TimeInterval(
                video_dl.Duration(1), video_dl.Duration(9)
            ).random_duration()
            self.assertGreaterEqual(dur, 1)
            self.assertLessEqual(dur, 9)

    def test_format(self):
        self.assertEqual(video_dl.Duration(-12).format(), "-12.0s")
        self.assertEqual(video_dl.Duration(119.9).format(), "2m0s")
        self.assertEqual(video_dl.Duration(1000).format(), "16m40s")


class TestFunctions(unittest.TestCase):
    def test_parse_log_level(self):
        default = 10  # = logging.DEBUG
        self.assertEqual(video_dl.parse_log_level("DEBUG"), 10)
        self.assertEqual(video_dl.parse_log_level("CRITICAL"), 50)
        self.assertEqual(video_dl.parse_log_level("BASIC_FORMAT"), default)
        self.assertEqual(video_dl.parse_log_level("<any>"), default)
        self.assertEqual(video_dl.parse_log_level("-1"), -1)
        with self.assertRaises(AttributeError):
            video_dl.parse_log_level(20)

    def test_promote_info_logs(self):
        logging.basicConfig(level=logging.DEBUG)
        logger = logging.getLogger()
        logger.debug = video_dl.promote_info_logs(logger.debug)
        with self.assertLogs(level=logging.INFO):
            logger.debug("[info] Promoted to info")
        with self.assertLogs(level=logging.DEBUG):
            logger.debug("[debug] Matches and remains at debug")
        with self.assertLogs(level=logging.WARNING):
            logger.warning("[warning] Warnings not affected")


class TestMyDateRange(unittest.TestCase):
    """Make sure `MyDateRange` inherits the features we expect."""

    @staticmethod
    def _today():
        return datetime.datetime.now(tz=datetime.timezone.utc).date()

    def test_daterange(self):
        century_21 = video_dl.MyDateRange("20000101", "21000101")
        self.assertFalse("19991231" in century_21)
        self.assertIn("20500615", century_21)
        common_era = video_dl.MyDateRange("00010101")
        self.assertTrue("19690721" in common_era)

    def test_default_values(self):
        my_date_range = video_dl.MyDateRange()
        self.assertIn(self._today(), my_date_range)

    def test_date_from_str(self):
        recent = video_dl.MyDateRange(start="today-6day")
        self.assertIn(self._today(), recent)
        self.assertNotIn(datetime.date(2005, 4, 3), recent)
        old = video_dl.MyDateRange(end="today-6days")
        self.assertNotIn(self._today(), old)
        self.assertIn(datetime.date(2005, 4, 3), old)


class TestConfigParse(unittest.TestCase):
    def setUp(self):
        self.config = configparser.ConfigParser()

    def test_empty_config(self):
        self.assertEqual(list(video_dl.parse_config(self.config)), [])

    def test_bad_job_identifier(self):
        with self.assertLogs(level=logging.ERROR):
            jobs = list(video_dl.parse_config(self.config, "job-id"))
        self.assertEqual(jobs, [])

    def test_minimal_config(self):
        string = "[job-id]\nSource=/dev/null\nSubDir=/dev/null\n"
        self.config.read_string(string)
        with self.assertLogs(level=logging.WARNING):
            jobs = list(video_dl.parse_config(self.config))
        self.assertEqual(jobs, [])


if __name__ == "__main__":
    unittest.main()
