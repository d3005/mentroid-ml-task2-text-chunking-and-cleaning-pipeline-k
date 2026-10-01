"""
Pack whole sentences into overlapping chunks of at most ``max_words`` words.

Algorithm (greedy, single pass, O(number of sentences)):

1. Start a chunk with the overlap carried from the previous chunk.
2. Add the next sentence while the chunk stays within ``max_words``.
3. When the next sentence would not fit, close the chunk. The trailing
   sentences of the closed chunk whose total is at most ``overlap_words``
   are carried into the next chunk. At least one sentence is carried even
   if it alone exceeds ``overlap_words``, provided it is at most half of
   ``max_words`` (otherwise the chunks would be mostly repetition).

Guarantees, all checked by the tests:

- **No sentence is ever cut.** Every chunk is a run of whole, consecutive
  sentences, so its text equals ``" ".join(sentences[start:end])``.
- **Size.** No chunk exceeds ``max_words``, except a single sentence that is
  longer than ``max_words`` on its own. It becomes its own chunk with
  ``oversized=True``, because cutting it would break the main rule.
- **Overlap.** Consecutive chunks share their boundary sentence(s), unless
  carrying even one sentence would leave no room for a new sentence (only
  possible next to a very long sentence). ``overlap_words`` records it.
- **Coverage and progress.** Every sentence appears in at least one chunk,
  in order, and each chunk adds at least one new sentence, so the loop
  always ends.
- **Determinism.** The same input and settings give the same chunks.
"""

import re
from dataclasses import asdict, dataclass
from typing import List

_WORD = re.compile(r"[^\W_]+(?:['\-][^\W_]+)*", re.UNICODE)


def count_words(text: str) -> int:
    """Words are runs of letters/digits; "don't" and "well-known" count once."""
    return len(_WORD.findall(text))


@dataclass(frozen=True)
class Chunk:
    chunk_id: int
    text: str
    word_count: int
    sentence_start: int        # index of first sentence (inclusive)
    sentence_end: int          # index after the last sentence (exclusive)
    overlap_words: int         # words shared with the previous chunk
    overlap_sentences: int     # sentences shared with the previous chunk
    oversized: bool            # one sentence longer than max_words

    def to_dict(self) -> dict:
        return asdict(self)


def _overlap_start(counts: List[int], start: int, end: int,
                   overlap_words: int, max_words: int, next_count: int) -> int:
    """First sentence index to carry into the next chunk (``end`` = none)."""
    if overlap_words <= 0 or end - start <= 1:
        return end
    carry, total = end, 0
    while carry - 1 > start:                       # never carry the whole chunk
        candidate = counts[carry - 1]
        if carry != end and total + candidate > overlap_words:
            break
        if carry == end and candidate > max_words // 2:
            break                                  # one huge sentence: skip overlap
        if total + candidate + next_count > max_words:
            break                                  # leave room for new text
        total += candidate
        carry -= 1
    return carry


def chunk_sentences(sentences: List[str], max_words: int = 200,
                    overlap_words: int = 40) -> List[Chunk]:
    if max_words <= 0:
        raise ValueError("max_words must be positive")
    if overlap_words < 0 or overlap_words >= max_words:
        raise ValueError("overlap_words must be in [0, max_words)")

    sentences = [s.strip() for s in sentences if s and s.strip()]
    counts = [count_words(s) for s in sentences]
    chunks: List[Chunk] = []
    start, i, carried = 0, 0, 0

    while i < len(sentences):
        end, total = i, sum(counts[start:i])
        while end < len(sentences) and (total + counts[end] <= max_words
                                        or end == start):
            total += counts[end]
            end += 1
            if total > max_words:                  # single oversized sentence
                break

        chunks.append(Chunk(
            chunk_id=len(chunks),
            text=" ".join(sentences[start:end]),
            word_count=total,
            sentence_start=start,
            sentence_end=end,
            overlap_words=sum(counts[start:start + carried]),
            overlap_sentences=carried,
            oversized=(end - start == 1 and total > max_words),
        ))
        if end >= len(sentences):
            break
        next_start = _overlap_start(counts, start, end, overlap_words,
                                    max_words, counts[end])
        carried = end - next_start
        start, i = next_start, end

    return chunks
