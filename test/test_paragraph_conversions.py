import io
from unittest.mock import Mock, patch

import pytest

from criaparse.models import ElementType


def make_mock_paragraphs(texts):
    class P:
        def __init__(self, text):
            self.text = text

    return [P(t) for t in texts]


def test_split_document_aggregates_and_splits():
    # Import module under test
    import criaparse.parsers.paragraph.conversions as conv

    # Reduce section_length to exercise branching logic
    original_len = conv.section_length
    conv.section_length = 3

    try:
        # paragraphs with word-counts that cause both append branches
        texts = ["one two", "three four five", "six seven eight nine", "ten"]
        mock_doc = Mock()
        mock_doc.paragraphs = make_mock_paragraphs(texts)

        sections = conv.split_document(mock_doc)

        # Expect it to split into sections based on the small section_length
        assert isinstance(sections, list)
        # There should be at least two sections
        assert len(sections) >= 2
        # Reconstruct joined text to ensure all paragraphs are present
        joined = " ".join([p.text for p in mock_doc.paragraphs])
        assert all(word in joined for s in sections for word in s.split())
    finally:
        conv.section_length = original_len


def test_convert_to_json_basic():
    import criaparse.parsers.paragraph.conversions as conv

    sections = ["First section text.", "Second section text."]
    nodes = conv.convert_to_json(sections)

    assert isinstance(nodes, list)
    assert len(nodes) == 2
    assert nodes[0]["node_number"] == 0
    assert nodes[1]["node_number"] == 1
    assert nodes[0]["type"] == "NarrativeText"
    assert "languages" in nodes[0]["metadata"]


def test_run_converter_creates_elements_from_document():
    # Patch the Document constructor used inside the conversions module so it returns a mock
    import criaparse.parsers.paragraph.conversions as conv

    mock_document = Mock()
    # a single paragraph -> single section
    mock_document.paragraphs = make_mock_paragraphs(["Hello world"])

    with patch.object(conv, "Document", return_value=mock_document):
        # run_converter accepts a file-like buffer but we patched Document so content is ignored
        elements = conv.run_converter(io.BytesIO(b"dummy content"))

    assert isinstance(elements, list)
    assert len(elements) == 1
    elem = elements[0]
    # ElementType.NARRATIVE_TEXT enum maps from string in convert_to_json
    assert elem.type == ElementType.NARRATIVE_TEXT
    assert "Hello world" in elem.text


def test_run_converter_empty_document_returns_empty_list():
    import criaparse.parsers.paragraph.conversions as conv

    mock_document = Mock()
    mock_document.paragraphs = []

    with patch.object(conv, "Document", return_value=mock_document):
        elements = conv.run_converter(io.BytesIO(b"dummy content"))

    assert isinstance(elements, list)
    assert elements == []


def test_split_document_exact_boundary_merges():
    import criaparse.parsers.paragraph.conversions as conv

    # Temporarily set section_length to 4 (words) so we can create exact boundary case
    original_len = conv.section_length
    conv.section_length = 4
    try:
        texts = ["one two", "three four"]
        mock_doc = Mock()
        mock_doc.paragraphs = make_mock_paragraphs(texts)

        sections = conv.split_document(mock_doc)
        # With <= behaviour the two paragraphs should be merged into one section
        assert len(sections) == 1
        assert "one two three four" in sections[0]
    finally:
        conv.section_length = original_len
