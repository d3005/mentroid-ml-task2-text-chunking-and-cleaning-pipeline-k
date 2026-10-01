"""
Turn messy book text into clean, single-spaced paragraphs.

Steps, in order (each is a small public function so it can be tested alone):

1. ``normalise_unicode``   NFKC, smart quotes -> ASCII quotes, en/em dashes
                           and "--" -> " - ", ellipsis character -> "...".
2. ``split_paragraphs``    CRLF -> LF; paragraphs are separated by blank lines.
3. ``is_heading``          drop paragraphs that are headings, not prose:
                           Roman/Arabic section numbers ("I.", "XII", "3."),
                           short ALL-CAPS lines ("ADVENTURE I. A SCANDAL IN
                           BOHEMIA") and "[Illustration]"-style tags.
4. ``strip_special``       remove characters outside the allowed set, e.g.
                           Gutenberg's _italics_ underscores, *, #, [ ], {, },
                           |, ~, ^, <, >, and stray symbols. Sentence
                           punctuation is KEPT because the sentence splitter
                           needs it.
5. ``normalise_whitespace`` unwrap hard line breaks inside a paragraph and
                           collapse every run of whitespace to one space.

Allowed characters: letters (any script), digits, whitespace and
    . , ! ? ; : ' " - ( ) & %
"""

import re
import unicodedata
from typing import List

_TRANSLATE = str.maketrans({
    "‘": "'", "’": "'", "‚": "'", "‛": "'",
    "′": "'", "´": "'", "`": "'",
    "“": '"', "”": '"', "„": '"', "‟": '"', "″": '"',
    "«": '"', "»": '"',
    "–": " - ", "—": " - ", "―": " - ", "−": "-",
    "…": "...",
    " ": " ", " ": " ", "​": "", "﻿": "",
})

_ROMAN_OR_NUMBER = re.compile(
    r"^(?:(?:chapter|book|part|section)\s+)?"
    r"(?:[ivxlcdm]+|\d+)\.?$",
    re.IGNORECASE,
)
_BRACKET_TAG = re.compile(r"^\[[^\]]{0,80}\]$")
_INLINE_TAG = re.compile(r"\[(?:illustration|footnote|sidenote)[^\]]*\]", re.IGNORECASE)
_DISALLOWED = re.compile(r"[^\w\s.,!?;:'\"()\-&%]|_", re.UNICODE)
_SPACE_BEFORE_PUNCT = re.compile(r"\s+([.,!?;:])")
_WHITESPACE = re.compile(r"\s+")
_BLANK_LINES = re.compile(r"\n\s*\n")
_DOUBLE_DASH = re.compile(r"\s*-{2,}\s*")


def normalise_unicode(text: str) -> str:
    text = unicodedata.normalize("NFKC", text)
    text = text.translate(_TRANSLATE)
    return _DOUBLE_DASH.sub(" - ", text)


def split_paragraphs(text: str) -> List[str]:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    return [p for p in _BLANK_LINES.split(text) if p.strip()]


def is_heading(paragraph: str, max_heading_words: int = 12) -> bool:
    """True for section numbers, short ALL-CAPS titles and [tags]."""
    line = _WHITESPACE.sub(" ", paragraph).strip()
    if not line:
        return True
    if _ROMAN_OR_NUMBER.match(line) or _BRACKET_TAG.match(line):
        return True
    letters = [c for c in line if c.isalpha()]
    words = line.split()
    return (
        len(words) <= max_heading_words
        and len(letters) >= 2
        and all(c.isupper() for c in letters)
        and not line.endswith(("?", "!", ","))
    )


def strip_special(text: str) -> str:
    text = _INLINE_TAG.sub(" ", text)
    return _DISALLOWED.sub(" ", text)


def normalise_whitespace(text: str) -> str:
    text = _WHITESPACE.sub(" ", text).strip()
    return _SPACE_BEFORE_PUNCT.sub(r"\1", text)


def clean_paragraphs(text: str, drop_headings: bool = True) -> List[str]:
    """Run every cleaning step and return the non-empty prose paragraphs."""
    if not isinstance(text, str):
        raise TypeError("text must be a str")
    paragraphs = []
    for raw in split_paragraphs(normalise_unicode(text)):
        if drop_headings and is_heading(raw):
            continue
        cleaned = normalise_whitespace(strip_special(raw))
        if any(c.isalnum() for c in cleaned):
            paragraphs.append(cleaned)
    return paragraphs


def clean_text(text: str, drop_headings: bool = True) -> str:
    """Cleaned text: one paragraph per block, separated by a blank line."""
    return "\n\n".join(clean_paragraphs(text, drop_headings))
