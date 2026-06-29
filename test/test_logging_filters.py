import logging
import os
from pathlib import Path

# Ensure app.core.config can load dotenv during import in test context.
os.environ.setdefault("ENV_PATH", str((Path(__file__).resolve().parents[1] / ".env").resolve()))

from app.core.app import SemanticImageDownloadTracebackFilter


def test_semantic_image_warning_traceback_is_removed():
    filt = SemanticImageDownloadTracebackFilter()
    record = logging.LogRecord(
        name="root",
        level=logging.WARNING,
        pathname=__file__,
        lineno=10,
        msg="Failed to download an image for a file. This can most likely be ignored.",
        args=(),
        exc_info=(Exception, Exception("boom"), None),
    )

    allowed = filt.filter(record)

    assert allowed is True
    assert record.exc_info is None
    assert "continuing without image caption data" in str(record.msg)


def test_semantic_image_warning_is_logged_only_once():
    filt = SemanticImageDownloadTracebackFilter()

    first = logging.LogRecord(
        name="root",
        level=logging.WARNING,
        pathname=__file__,
        lineno=22,
        msg="Failed to download image abc123, removing from processing",
        args=(),
        exc_info=None,
    )
    second = logging.LogRecord(
        name="root",
        level=logging.WARNING,
        pathname=__file__,
        lineno=23,
        msg="Failed to download image def456, removing from processing",
        args=(),
        exc_info=None,
    )

    assert filt.filter(first) is True
    assert filt.filter(second) is False


def test_unrelated_warning_keeps_exc_info():
    filt = SemanticImageDownloadTracebackFilter()
    original_exc_info = (Exception, Exception("boom"), None)
    record = logging.LogRecord(
        name="root",
        level=logging.WARNING,
        pathname=__file__,
        lineno=48,
        msg="Some other warning",
        args=(),
        exc_info=original_exc_info,
    )

    allowed = filt.filter(record)

    assert allowed is True
    assert record.exc_info == original_exc_info
