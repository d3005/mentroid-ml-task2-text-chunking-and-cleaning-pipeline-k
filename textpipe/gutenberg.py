"""
Remove Project Gutenberg's licence header and footer.

Every Gutenberg .txt file wraps the book in boilerplate: a title/licence
block before a ``*** START OF ... ***`` line and the full licence after an
``*** END OF ... ***`` line. That text is not part of the book and would
otherwise end up in the chunks, so it is cut first.

The marker wording has changed over the years ("THIS PROJECT GUTENBERG",
"THE PROJECT GUTENBERG", with or without "EBOOK"), so matching is
deliberately loose. If no marker is found the text is returned unchanged.
"""

import re
from dataclasses import dataclass

_START = re.compile(
    r"^\s*\*{3}\s*START OF (?:THIS|THE) PROJECT GUTENBERG.*?\*{3}\s*$",
    re.IGNORECASE | re.MULTILINE,
)
_END = re.compile(
    r"^\s*\*{3}\s*END OF (?:THIS|THE) PROJECT GUTENBERG.*?\*{3}\s*$",
    re.IGNORECASE | re.MULTILINE,
)
# Very old files end with "End of the Project Gutenberg EBook of ..." and no stars.
_END_PLAIN = re.compile(
    r"^\s*End of (?:the |this )?Project Gutenberg.*$",
    re.IGNORECASE | re.MULTILINE,
)


@dataclass(frozen=True)
class StripResult:
    text: str
    found_start: bool
    found_end: bool
    removed_chars: int


def strip_gutenberg_boilerplate(text: str) -> StripResult:
    """Return the text between the START and END markers (exclusive)."""
    if not isinstance(text, str):
        raise TypeError("text must be a str")

    begin, end = 0, len(text)
    start_match = _START.search(text)
    if start_match:
        begin = start_match.end()

    end_match = _END.search(text, begin) or _END_PLAIN.search(text, begin)
    if end_match:
        end = end_match.start()

    body = text[begin:end]
    return StripResult(
        text=body,
        found_start=start_match is not None,
        found_end=end_match is not None,
        removed_chars=len(text) - len(body),
    )
