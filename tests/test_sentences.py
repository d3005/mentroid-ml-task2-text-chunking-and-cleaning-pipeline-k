import pytest

from textpipe.sentences import split_paragraphs_into_sentences, split_sentences


@pytest.mark.parametrize("text, expected", [
    ("One. Two! Three?", ["One.", "Two!", "Three?"]),
    ("Mr. Holmes met Dr. Watson. They talked.",
     ["Mr. Holmes met Dr. Watson.", "They talked."]),
    ("Mrs. Hudson and St. Simon came. Then left.",
     ["Mrs. Hudson and St. Simon came.", "Then left."]),
    ("A. Conan Doyle wrote it. J. R. R. Tolkien too.",
     ["A. Conan Doyle wrote it.", "J. R. R. Tolkien too."]),
    ("It was more than I. Then we left.", ["It was more than I.", "Then we left."]),
    ("He lives at No. 221 Baker Street. Yes.",
     ["He lives at No. 221 Baker Street.", "Yes."]),
    ('"No. I disagree." He frowned.', ['"No.', 'I disagree."', "He frowned."]),
    ("Use tools e.g. hammers. Done.", ["Use tools e.g. hammers.", "Done."]),
    ('"Who is it?" said he. "A friend."', ['"Who is it?" said he.', '"A friend."']),
    ('"Stop!" cried Holmes. We stopped.', ['"Stop!" cried Holmes.', "We stopped."]),
    ("Wait... What happened?", ["Wait...", "What happened?"]),
    ("It cost 5.50 pounds. Cheap.", ["It cost 5.50 pounds.", "Cheap."]),
    ("He said (quietly.) Then left.", ["He said (quietly.)", "Then left."]),
    ("Chapter ends with a colon:", ["Chapter ends with a colon:"]),
    ("Version 2. Next line.", ["Version 2.", "Next line."]),
])
def test_split_sentences(text, expected):
    assert split_sentences(text) == expected


def test_text_is_preserved_exactly():
    text = 'Mr. A said "Hi!" to B. Then C, D. E left? F stayed.'
    assert " ".join(split_sentences(text)) == text


def test_empty():
    assert split_sentences("") == []
    assert split_sentences("   ") == []


def test_sentences_never_span_paragraphs():
    assert split_paragraphs_into_sentences(["no end here", "Next one."]) == \
        ["no end here", "Next one."]
