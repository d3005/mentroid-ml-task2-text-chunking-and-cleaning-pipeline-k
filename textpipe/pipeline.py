"""
End-to-end pipeline: raw Gutenberg text -> cleaned text -> sentences -> chunks.
"""

import json
import statistics
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from .chunking import Chunk, chunk_sentences, count_words
from .cleaning import clean_paragraphs
from .gutenberg import strip_gutenberg_boilerplate
from .sentences import split_paragraphs_into_sentences


@dataclass
class PipelineResult:
    source: str
    cleaned_text: str
    sentences: List[str]
    chunks: List[Chunk]
    stats: dict = field(default_factory=dict)


def run(raw_text: str, max_words: int = 200, overlap_words: int = 40,
        source: str = "<text>") -> PipelineResult:
    stripped = strip_gutenberg_boilerplate(raw_text)
    paragraphs = clean_paragraphs(stripped.text)
    sentences = split_paragraphs_into_sentences(paragraphs)
    chunks = chunk_sentences(sentences, max_words=max_words,
                             overlap_words=overlap_words)
    cleaned = "\n\n".join(paragraphs)
    return PipelineResult(
        source=source,
        cleaned_text=cleaned,
        sentences=sentences,
        chunks=chunks,
        stats=_stats(raw_text, stripped, paragraphs, sentences, chunks,
                     max_words, overlap_words),
    )


def _stats(raw_text, stripped, paragraphs, sentences, chunks,
           max_words, overlap_words) -> dict:
    sizes = [c.word_count for c in chunks]
    overlaps = [c.overlap_words for c in chunks[1:]]
    return {
        "settings": {"max_words": max_words, "overlap_words": overlap_words},
        "input": {
            "raw_chars": len(raw_text),
            "raw_words": count_words(raw_text),
            "gutenberg_header_found": stripped.found_start,
            "gutenberg_footer_found": stripped.found_end,
            "boilerplate_chars_removed": stripped.removed_chars,
        },
        "cleaned": {
            "chars": sum(len(p) for p in paragraphs) + 2 * max(len(paragraphs) - 1, 0),
            "words": sum(count_words(p) for p in paragraphs),
            "paragraphs": len(paragraphs),
            "sentences": len(sentences),
        },
        "chunks": {
            "count": len(chunks),
            "min_words": min(sizes) if sizes else 0,
            "max_words": max(sizes) if sizes else 0,
            "mean_words": round(statistics.mean(sizes), 1) if sizes else 0,
            "median_words": statistics.median(sizes) if sizes else 0,
            "oversized": sum(c.oversized for c in chunks),
            "mean_overlap_words": round(statistics.mean(overlaps), 1) if overlaps else 0,
            "boundaries_without_overlap": sum(o == 0 for o in overlaps),
        },
    }


def write_outputs(result: PipelineResult, out_dir: Path) -> List[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    paths = {
        "cleaned": out_dir / "cleaned.txt",
        "chunks": out_dir / "chunks.jsonl",
        "stats": out_dir / "stats.json",
    }
    paths["cleaned"].write_text(result.cleaned_text + "\n", encoding="utf-8")
    with paths["chunks"].open("w", encoding="utf-8") as handle:
        for chunk in result.chunks:
            handle.write(json.dumps(chunk.to_dict(), ensure_ascii=False) + "\n")
    paths["stats"].write_text(
        json.dumps({"source": result.source, **result.stats}, indent=2) + "\n",
        encoding="utf-8")
    return list(paths.values())


def run_file(path: Path, out_dir: Optional[Path] = None, **kwargs) -> PipelineResult:
    raw = Path(path).read_text(encoding="utf-8", errors="replace")
    result = run(raw, source=str(path), **kwargs)
    if out_dir is not None:
        write_outputs(result, Path(out_dir))
    return result
