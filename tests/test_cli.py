import subprocess
import unittest

import video_dl

EXE_NAME = "video-dl"


class TestCLI(unittest.TestCase):
    def test_version(self):
        proc = subprocess.run(
            [EXE_NAME, "--version"], encoding="utf-8", capture_output=True, check=True
        )
        self.assertIn(EXE_NAME, proc.stdout)
        self.assertIn(video_dl.__version__, proc.stdout)
