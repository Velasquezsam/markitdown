import io
from types import SimpleNamespace
from unittest.mock import Mock

from markitdown import DocumentConverterResult, StreamInfo
from markitdown._streamlit_app import (
    conversion_counts,
    convert_uploaded_file,
    format_file_size,
    output_filename,
)


def test_output_filename_replaces_extension() -> None:
    assert output_filename("quarterly-report.pdf") == "quarterly-report.md"


def test_output_filename_uses_stem_for_multiple_suffixes() -> None:
    assert output_filename("archive.tar.gz") == "archive.tar.md"


def test_format_file_size_uses_compact_units() -> None:
    assert format_file_size(512) == "512 B"
    assert format_file_size(2048) == "2.0 KB"
    assert format_file_size(2 * 1024**2) == "2.0 MB"


def test_conversion_counts_include_failed_files() -> None:
    assert conversion_counts([("a.txt", "A")], [("b.pdf", "error")]) == (2, 1, 1)


def test_convert_uploaded_file_passes_stream_metadata() -> None:
    uploaded_file = SimpleNamespace(
        name="notes.txt",
        type="text/plain",
        getvalue=lambda: b"hello",
    )
    converter = Mock()
    converter.convert.return_value = DocumentConverterResult("# Hello")

    markdown = convert_uploaded_file(uploaded_file, converter)

    assert markdown == "# Hello"
    converter.convert.assert_called_once()
    (stream,) = converter.convert.call_args.args
    assert isinstance(stream, io.BytesIO)
    assert stream.read() == b"hello"
    assert converter.convert.call_args.kwargs["stream_info"] == StreamInfo(
        filename="notes.txt",
        extension=".txt",
        mimetype="text/plain",
    )
