import collections
import configparser
import datetime
import logging
import unittest

import video_dl


class TestProgram(unittest.TestCase):
    def setUp(self):
        config = configparser.ConfigParser(
            interpolation=configparser.ExtendedInterpolation())
        self.test_section = "SectionName"
        config.read_dict({self.test_section: {}})
        self.prog = video_dl.Program(config, self.test_section)

    def _assert_interval(self, n, lower, upper):
        self.assertGreaterEqual(n, lower)
        self.assertLessEqual(n, upper)

    def test_parse_interval_random(self):
        key = "TestInterval"
        # No value
        self.assertEqual(self.prog.parse_interval_random(key), 0.0)
        # Single valid value
        self.prog.map[key] = "2"
        for _ in range(4):
            interval = self.prog.parse_interval_random(key)
            self._assert_interval(interval, 0.0, 2.0)
        # Single invalid value
        self.prog.map[key] = "-1"
        with self.assertLogs(level="WARNING"):
            interval = self.prog.parse_interval_random(key)
        self.assertEqual(interval, 0.0)
        # Two valid values
        self.prog.map[key] = "3, 5"
        for _ in range(4):
            interval = self.prog.parse_interval_random(key)
            self._assert_interval(interval, 3.0, 5.0)
        # All values after first two are ignored
        self.prog.map[key] = "6, 7, 15, 0"
        for _ in range(4):
            interval = self.prog.parse_interval_random(key)
            self._assert_interval(interval, 6.0, 7.0)
        # One valid, one invalid
        self.prog.map[key] = "6, 8a"
        with self.assertLogs(level="WARNING"):
            interval = self.prog.parse_interval_random(key)
        self.assertEqual(interval, 0.0)
        # No dangling commas
        self.prog.map[key] = " 3,"
        with self.assertLogs(level="WARNING"):
            interval = self.prog.parse_interval_random(key)
        self.assertEqual(interval, 0.0)

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
            test = (value in msg and str(default) in msg and key in msg
                    for msg in recording.output)
            self.assertTrue(any(test))

    def test_interpret_options(self):
        opt_key = "VideoDL://options"
        options = {"key": "value",
                   opt_key: ["--quiet", "-R", "8"]}
        with self.assertLogs(level=logging.DEBUG):
            options = self.prog.interpret_options(options)
        # But don't assume we know what values our args will be parsed into
        self.assertIsInstance(options, collections.ChainMap)
        # Original argv is unmodified
        self.assertListEqual(options[opt_key],
                             ["--quiet", "-R", "8"])
        options[opt_key].append("--bad-option")
        with self.assertRaises(video_dl.yt_dlp.optparse.OptParseError):
            options = self.prog.interpret_options(options)


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

    def test_parse_duration(self):
        self.assertEqual(video_dl.duration("3.14"), 3.14)
        self.assertEqual(video_dl.duration("3600"), 3600)
        self.assertRaises(ValueError, video_dl.duration, "-1")
        self.assertRaises(ValueError, video_dl.duration, "inf")

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

    def test_daterange(self):
        _21_century = video_dl.MyDateRange("20000101", "21000101")
        self.assertFalse("19991231" in _21_century)
        self.assertIn("20500615", _21_century)
        _ac = video_dl.MyDateRange("00010101")
        self.assertTrue("19690721" in _ac)

    def test_default_values(self):
        my = video_dl.MyDateRange()
        self.assertIn(datetime.date.today(), my)

    def test_date_from_str(self):
        recent = video_dl.MyDateRange(start="today-6day")
        self.assertIn(datetime.date.today(), recent)
        self.assertNotIn(datetime.date(2005, 4, 3), recent)
        old = video_dl.MyDateRange(end="today-6days")
        self.assertNotIn(datetime.date.today(), old)
        self.assertIn(datetime.date(2005, 4, 3), old)


if __name__ == "__main__":
    unittest.main()
