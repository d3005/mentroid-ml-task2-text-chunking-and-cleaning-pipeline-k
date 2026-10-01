"""
Rule-based sentence splitter for cleaned English prose.

A boundary is placed after ``.``, ``!`` or ``?`` (optionally followed by
closing quotes or brackets) when the next token starts a new sentence:
an upper-case letter, a digit, or an opening quote/bracket followed by one.

It is NOT a boundary when:
- the word before the full stop is a known abbreviation ("Mr.", "Dr.",
  "St.", "e.g."), a single initial ("A. Conan Doyle", but never the pronoun
  "I."), or a number abbreviation followed by a digit ("No. 7");
- the next token starts with a lower-case letter, as in
  '"Who is it?" said he.' - the question mark ends the quote, not the
  sentence.

No third-party models are used, so the result is deterministic and works
offline. The trade-off is documented in the README.
"""

import re
from typing import List

ABBREVIATIONS = frozenset({
    "mr", "mrs", "ms", "messrs", "dr", "prof", "rev", "hon", "st", "sr", "jr",
    "capt", "col", "gen", "lt", "sgt", "maj", "adm", "gov", "pres", "sen", "rep",
    "mt", "ft", "ave", "rd", "ed", "eds", "co", "corp", "inc", "ltd", "dept", "est", "approx",
    "etc", "vs", "viz", "cf", "ie", "eg", "al", "jan", "feb", "mar", "apr", "jun",
    "jul", "aug", "sep", "sept", "oct", "nov", "dec",
})

# Abbreviations that only precede a number: "No. 7", "p. 12", "Vol. 2".
# "No." before a word is the answer "No." and does end a sentence.
NUMBER_ABBREVIATIONS = frozenset({"no", "nos", "vol", "vols", "ch", "chap",
                                  "p", "pp", "fig", "figs", "art", "sec"})

# Candidate end: terminal punctuation run, optional closing quotes/brackets,
# then whitespace.
_CANDIDATE = re.compile(r"[.!?]+['\")\]]*(?=\s+)")
_NEXT_STARTS_SENTENCE = re.compile(r"\s+['\"(\[]*[A-Z0-9]")
_LAST_WORD = re.compile(r"([A-Za-z][A-Za-z.]*)\.$")


def _is_abbreviation(text_before_and_dot: str, next_is_digit: bool) -> bool:
    match = _LAST_WORD.search(text_before_and_dot)
    if not match:
        return False
    word = match.group(1).lower()
    if word in NUMBER_ABBREVIATIONS:
        return next_is_digit
    if word == "i":
        return False                      # the pronoun: "...than I. Then"
    if len(word) == 1 and word.isalpha():
        return True                       # single initial: "J. Smith"
    if "." in word:                       # dotted forms: "e.g", "U.S"
        return True
    return word in ABBREVIATIONS


def split_sentences(paragraph: str) -> List[str]:
    """Split one cleaned paragraph into sentences (order and text preserved)."""
    text = paragraph.strip()
    if not text:
        return []
    sentences, start = [], 0
    for match in _CANDIDATE.finditer(text):
        end = match.end()
        nxt = _NEXT_STARTS_SENTENCE.match(text, end)
        if not nxt:
            continue
        punct = match.group(0)
        if punct.startswith(".") and len(punct.rstrip("'\")]")) == 1:
            if _is_abbreviation(text[start:match.start() + 1],
                                next_is_digit=nxt.group(0)[-1].isdigit()):
                continue
        piece = text[start:end].strip()
        if piece:
            sentences.append(piece)
        start = end
    tail = text[start:].strip()
    if tail:
        sentences.append(tail)
    return sentences


def split_paragraphs_into_sentences(paragraphs: List[str]) -> List[str]:
    """Sentences never span paragraphs, so split each paragraph separately."""
    out: List[str] = []
    for paragraph in paragraphs:
        out.extend(split_sentences(paragraph))
    return out
