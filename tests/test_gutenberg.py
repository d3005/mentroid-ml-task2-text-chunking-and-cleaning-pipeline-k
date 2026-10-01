from textpipe.gutenberg import strip_gutenberg_boilerplate

HEADER = "The Project Gutenberg EBook of Test\r\nLicence text...\r\n"
START = "*** START OF THIS PROJECT GUTENBERG EBOOK TEST ***\r\n"
END = "*** END OF THIS PROJECT GUTENBERG EBOOK TEST ***\r\n"
FOOTER = "Updated editions will replace the previous one.\r\nMore licence.\r\n"


def test_keeps_only_text_between_markers():
    result = strip_gutenberg_boilerplate(HEADER + START + "Body text.\r\n" + END + FOOTER)
    assert result.text.strip() == "Body text."
    assert result.found_start and result.found_end
    assert "licence" not in result.text.lower()


def test_newer_marker_wording():
    text = "*** START OF THE PROJECT GUTENBERG EBOOK X ***\nBody.\n*** END OF THE PROJECT GUTENBERG EBOOK X ***"
    assert strip_gutenberg_boilerplate(text).text.strip() == "Body."


def test_old_plain_end_marker():
    text = START + "Body.\nEnd of the Project Gutenberg EBook of Test\nlicence"
    result = strip_gutenberg_boilerplate(text)
    assert result.text.strip() == "Body." and result.found_end


def test_no_markers_returns_text_unchanged():
    result = strip_gutenberg_boilerplate("Just a plain text.")
    assert result.text == "Just a plain text."
    assert not result.found_start and not result.found_end
    assert result.removed_chars == 0


def test_rejects_non_string():
    import pytest
    with pytest.raises(TypeError):
        strip_gutenberg_boilerplate(None)
