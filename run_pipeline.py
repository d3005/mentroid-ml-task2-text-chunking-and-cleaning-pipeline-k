#!/usr/bin/env python3
"""
Clean a Project Gutenberg text file and split it into overlapping chunks.

    python run_pipeline.py                                  # default input
    python run_pipeline.py data/raw/my_book.txt --max-words 200 --overlap-words 40
"""

import argparse
import sys
from pathlib import Path

from textpipe.pipeline import run_file, write_outputs

DEFAULT_INPUT = Path("data/raw/sherlock_holmes_ch1_a_scandal_in_bohemia.txt")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("input", nargs="?", type=Path, default=DEFAULT_INPUT,
                        help=f"raw .txt file (default: {DEFAULT_INPUT})")
    parser.add_argument("-o", "--out-dir", type=Path, default=Path("output"),
                        help="where to write cleaned.txt, chunks.jsonl, stats.json")
    parser.add_argument("--max-words", type=int, default=200,
                        help="maximum words per chunk (default 200)")
    parser.add_argument("--overlap-words", type=int, default=40,
                        help="target words shared by consecutive chunks (default 40)")
    parser.add_argument("--preview", type=int, default=2,
                        help="number of chunks to print (default 2)")
    args = parser.parse_args(argv)

    if not args.input.is_file():
        parser.error(f"input file not found: {args.input} "
                     "(run scripts/fetch_chapter.py first)")
    try:
        result = run_file(args.input, max_words=args.max_words,
                          overlap_words=args.overlap_words)
    except ValueError as exc:
        parser.error(str(exc))
    paths = write_outputs(result, args.out_dir)

    s = result.stats
    c = s["chunks"]
    print(f"Input        {args.input}")
    print(f"Boilerplate  header={s['input']['gutenberg_header_found']} "
          f"footer={s['input']['gutenberg_footer_found']} "
          f"removed {s['input']['boilerplate_chars_removed']:,} chars")
    print(f"Cleaned      {s['cleaned']['words']:,} words, "
          f"{s['cleaned']['paragraphs']} paragraphs, {s['cleaned']['sentences']} sentences")
    print(f"Chunks       {c['count']} (words min {c['min_words']}, "
          f"mean {c['mean_words']}, max {c['max_words']}; oversized {c['oversized']})")
    print(f"Overlap      mean {c['mean_overlap_words']} words; "
          f"{c['boundaries_without_overlap']} boundaries without overlap")
    print("Wrote        " + ", ".join(str(p) for p in paths))
    for chunk in result.chunks[: max(args.preview, 0)]:
        print(f"\n--- chunk {chunk.chunk_id} ({chunk.word_count} words, "
              f"sentences {chunk.sentence_start}-{chunk.sentence_end - 1}, "
              f"overlap {chunk.overlap_words} words) ---")
        print(chunk.text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
