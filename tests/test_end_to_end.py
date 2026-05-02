import contextlib
import unittest.mock
from pathlib import Path

import pytest
import yt_dlp  # type: ignore

import video_dl


@pytest.fixture(
    name="mock_ydl",
    params=[
        pytest.param({"return_value": 0}, id="successful"),
        pytest.param(
            {"side_effect": yt_dlp.DownloadError("handle this error")},
            id="DownloadError",
        ),
    ],
)
def mock_ydl_fixture(
    request: pytest.FixtureRequest, monkeypatch: pytest.MonkeyPatch
) -> unittest.mock.MagicMock:
    """Mock the `yt_dlp.YoutubeDL` context manager."""
    mock_context = unittest.mock.MagicMock()
    mock_download_kwargs = request.param
    mock_context.download = unittest.mock.MagicMock(**mock_download_kwargs)

    @contextlib.contextmanager
    def mock_youtube_dl(params):
        mock_context.params = params
        yield mock_context

    monkeypatch.setattr(video_dl.yt_dlp, "YoutubeDL", mock_youtube_dl)
    return mock_context


def test_without_urls(tmp_path: Path, mock_ydl: unittest.mock.MagicMock) -> None:
    source_path = tmp_path / "source.txt"
    source_path.touch()
    subdir_path = tmp_path / "downloads"
    subdir_path.mkdir()
    config_path = tmp_path / "config"
    config_path.write_text(f"[test]\nSource={source_path}\nSubDir={subdir_path}\n")
    video_dl.main(["-d", "--config", str(config_path)])
    print(mock_ydl.params)
    outtmpl = mock_ydl.params["outtmpl"]
    assert outtmpl.startswith(str(subdir_path))
    mock_ydl.download.assert_called_once_with([])
