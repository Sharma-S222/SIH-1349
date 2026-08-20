"""Tests for RTSP URL sanitization."""
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

import pytest

from integration.video.security import sanitize_rtsp_url, has_credentials


class TestSanitizeRtspUrl:
    def test_with_credentials(self):
        url = "rtsp://admin:secret123@192.168.1.10/stream"
        result = sanitize_rtsp_url(url)
        assert "admin" not in result
        assert "secret123" not in result
        assert "***:***@" in result
        assert "192.168.1.10" in result
        assert "/stream" in result

    def test_without_credentials(self):
        url = "rtsp://192.168.1.10/stream"
        result = sanitize_rtsp_url(url)
        assert result == url

    def test_with_port(self):
        url = "rtsp://admin:pass@192.168.1.10:554/stream"
        result = sanitize_rtsp_url(url)
        assert "admin" not in result
        assert "pass" not in result
        assert "***:***@" in result
        assert "192.168.1.10:554" in result

    def test_empty_string(self):
        result = sanitize_rtsp_url("")
        assert result == ""

    def test_malformed_url(self):
        result = sanitize_rtsp_url("not-a-url")
        # Should not crash
        assert isinstance(result, str)


class TestHasCredentials:
    def test_with_credentials(self):
        assert has_credentials("rtsp://admin:pass@192.168.1.10/stream") is True

    def test_without_credentials(self):
        assert has_credentials("rtsp://192.168.1.10/stream") is False

    def test_empty(self):
        assert has_credentials("") is False
