#!/usr/bin/env python3
"""
Download a public-domain book from Project Gutenberg and save one chapter
as the pipeline's input, keeping Gutenberg's own header and footer so the
pipeline's boilerplate stripping is exercised on real data.

Default: "The Adventures of Sherlock Holmes" by Arthur Conan Doyle
(Gutenberg eBook #1661), chapter I, "A Scandal in Bohemia".

    python scripts/fetch_chapter.py
    python scripts/fetch_chapter.py --book 1342 --start "Chapter 1" --end "Chapter 2" \
        --out data/raw/pride_and_prejudice_ch1.txt

If gutenberg.org is unreachable, the GITenberg mirror of the same file on
GitHub is tried.
"""

import argparse
import re
import sys
import urllib.request
from pathlib import Path

SOURCES = [
    "https://www.gutenberg.org/cache/epub/{book}/pg{book}.txt",
    "https://www.gutenberg.org/files/{book}/{book}-0.txt",
    "https://raw.githubusercontent.com/GITenberg/{slug}/master/{book}.txt",
]
DEFAULT_SLUG = "The-Adventures-of-Sherlock-Holmes_1661"
START_MARK = re.compile(r"^\s*\*{3}\s*START OF (?:THIS|THE) PROJECT GUTENBERG.*$",
                        re.IGNORECASE | re.MULTILINE)
END_MARK = re.compile(r"^\s*\*{3}\s*END OF (?:THIS|THE) PROJECT GUTENBERG.*$",
                      re.IGNORECASE | re.MULTILINE)


def download(book: int, slug: str) -> str:
    errors = []
    for template in SOURCES:
        url = template.format(book=book, slug=slug)
        try:
            with urllib.request.urlopen(url, timeout=30) as response:
                print(f"Downloaded {url}")
                return response.read().decode("utf-8-sig", errors="replace")
        except Exception as exc:  # network errors vary by platform
            errors.append(f"{url}: {exc}")
    raise SystemExit("Could not download the book:\n  " + "\n  ".join(errors))


def extract_chapter(text: str, start: str, end: str) -> str:
    """Gutenberg header + text from the `start` line up to the `end` line + footer."""
    start_mark, end_mark = START_MARK.search(text), END_MARK.search(text)
    if not (start_mark and end_mark):
        raise SystemExit("Gutenberg START/END markers not found")
    body = text[start_mark.end():end_mark.start()]
    begin = re.search(rf"^{re.escape(start)}", body, re.MULTILINE)
    if not begin:
        raise SystemExit(f"Chapter start not found: {start!r}")
    finish = re.search(rf"^{re.escape(end)}", body[begin.end():], re.MULTILINE)
    stop = begin.end() + finish.start() if finish else len(body)
    header = text[:start_mark.end()]
    footer = text[end_mark.start():]
    return header + "\n\n" + body[begin.start():stop].rstrip() + "\n\n\n" + footer


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--book", type=int, default=1661)
    parser.add_argument("--slug", default=DEFAULT_SLUG,
                        help="GITenberg repository name, used for the fallback mirror")
    parser.add_argument("--start", default="ADVENTURE I. A SCANDAL IN BOHEMIA")
    parser.add_argument("--end", default="ADVENTURE II. THE RED-HEADED LEAGUE")
    parser.add_argument("--out", type=Path,
                        default=Path("data/raw/sherlock_holmes_ch1_a_scandal_in_bohemia.txt"))
    args = parser.parse_args(argv)

    chapter = extract_chapter(download(args.book, args.slug), args.start, args.end)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    # newline="" keeps the original CRLF line endings: messy input on purpose.
    with open(args.out, "w", encoding="utf-8", newline="") as handle:
        handle.write(chapter)
    print(f"Saved {args.out} ({len(chapter):,} chars)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
