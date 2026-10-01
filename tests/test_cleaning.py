import pytest

from textpipe.cleaning import (clean_paragraphs, clean_text, is_heading,
                               normalise_unicode, normalise_whitespace,
                               strip_special)


def test_crlf_hard_wraps_and_runs_of_spaces_are_normalised():
    raw = "It was a   dark\r\nnight,\tand the\r\n  rain fell.\r\n\r\n\r\nNew   paragraph."
    assert clean_paragraphs(raw) == ["It was a dark night, and the rain fell.",
                                     "New paragraph."]


def test_smart_quotes_dashes_and_ellipsis_become_ascii():
    text = normalise_unicode("“Hello,” she said—it’s late…")
    assert text == "\"Hello,\" she said - it's late..."


def test_double_hyphen_becomes_spaced_dash():
    assert clean_text("the observer--excellent for") == "the observer - excellent for"


def test_special_characters_removed_but_sentence_punctuation_kept():
    raw = "_Italic_ word, *bold* #tag [Illustration] {x} <y> |z| ~ ^ © 2024! Ok? Yes; no: (maybe) 50% & 'q' \"d\"."
    out = clean_text(raw)
    for bad in "_*#[]{}<>|~^©":
        assert bad not in out
    for keep in ".,!?;:()%&'\"":
        assert keep in out
    assert "Illustration" not in out
    assert out.startswith("Italic word, bold tag")


def test_non_english_letters_survive():
    assert clean_text("Café naïve façade.") == "Café naïve façade."


@pytest.mark.parametrize("line", ["I.", "XII.", "iv", "3.", "CHAPTER IV", "Chapter 12.",
                                  "ADVENTURE I. A SCANDAL IN BOHEMIA", "[Illustration]"])
def test_headings_are_detected(line):
    assert is_heading(line)


@pytest.mark.parametrize("line", ["I am here.", "To Sherlock Holmes she is always THE woman.",
                                  "WHAT ARE YOU DOING?", "OK, GO!",
                                  "THIS LINE IS FAR TOO LONG TO BE A HEADING BECAUSE IT KEEPS ON GOING AND GOING"])
def test_prose_is_not_a_heading(line):
    assert not is_heading(line)


def test_headings_can_be_kept():
    assert clean_paragraphs("CHAPTER I\n\nText.", drop_headings=False) == ["CHAPTER I", "Text."]


def test_space_before_punctuation_removed():
    assert normalise_whitespace("Hello , world !") == "Hello, world!"


def test_paragraph_of_only_symbols_is_dropped():
    assert clean_paragraphs("* * * * *\n\nReal text.") == ["Real text."]


def test_empty_and_whitespace_only_input():
    assert clean_paragraphs("") == []
    assert clean_paragraphs(" \r\n\t\n ") == []
    assert strip_special("") == ""


def test_rejects_non_string():
    with pytest.raises(TypeError):
        clean_paragraphs(123)
