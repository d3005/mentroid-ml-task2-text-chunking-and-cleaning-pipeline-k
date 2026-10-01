import random

import pytest

from textpipe.chunking import chunk_sentences, count_words


def _sentences(lengths):
    return [" ".join([f"w{i}x{j}" for j in range(n - 1)] + [f"end{i}."])
            for i, n in enumerate(lengths)]


def check_invariants(sentences, chunks, max_words, overlap_words):
    """Every guarantee from the chunking module docstring."""
    counts = [count_words(s) for s in sentences]
    assert chunks or not sentences
    covered = set()
    for k, chunk in enumerate(chunks):
        assert chunk.chunk_id == k
        # whole sentences only: text is exactly a run of consecutive sentences
        assert chunk.text == " ".join(sentences[chunk.sentence_start:chunk.sentence_end])
        assert chunk.word_count == count_words(chunk.text)
        if chunk.oversized:
            assert chunk.sentence_end - chunk.sentence_start == 1
            assert chunk.word_count > max_words
        else:
            assert chunk.word_count <= max_words
        covered.update(range(chunk.sentence_start, chunk.sentence_end))
        if k:
            prev = chunks[k - 1]
            # overlap is exactly the shared sentences, and progress is made
            assert chunk.sentence_start == prev.sentence_end - chunk.overlap_sentences
            assert chunk.sentence_end > prev.sentence_end
            assert chunk.overlap_words == sum(counts[chunk.sentence_start:prev.sentence_end])
            if chunk.overlap_words > overlap_words:
                # only allowed for one forced sentence, capped at half a chunk
                assert chunk.overlap_sentences == 1
                assert chunk.overlap_words <= max_words // 2
        else:
            assert chunk.overlap_words == 0 and chunk.sentence_start == 0
    assert covered == set(range(len(sentences)))


def test_count_words():
    assert count_words("Don't stop - it's a well-known fact, 2024!") == 7
    assert count_words("  - ... !! ") == 0


def test_basic_packing_and_overlap():
    sentences = _sentences([5, 5, 5, 5, 5, 5])
    chunks = chunk_sentences(sentences, max_words=12, overlap_words=5)
    assert [(c.sentence_start, c.sentence_end) for c in chunks] == [(0, 2), (1, 3), (2, 4), (3, 5), (4, 6)]
    assert all(c.overlap_words == 5 for c in chunks[1:])
    check_invariants(sentences, chunks, 12, 5)


def test_overlap_takes_several_short_sentences():
    sentences = _sentences([10, 3, 3, 3, 10])
    chunks = chunk_sentences(sentences, max_words=20, overlap_words=6)
    assert chunks[1].overlap_sentences == 2 and chunks[1].overlap_words == 6
    check_invariants(sentences, chunks, 20, 6)


def test_no_overlap_option():
    sentences = _sentences([4] * 10)
    chunks = chunk_sentences(sentences, max_words=10, overlap_words=0)
    assert all(c.overlap_words == 0 for c in chunks)
    assert sum(c.word_count for c in chunks) == 40
    check_invariants(sentences, chunks, 10, 0)


def test_oversized_sentence_is_kept_whole_in_its_own_chunk():
    sentences = _sentences([5, 250, 5])
    chunks = chunk_sentences(sentences, max_words=200, overlap_words=40)
    oversized = [c for c in chunks if c.oversized]
    assert len(oversized) == 1 and oversized[0].word_count == 250
    assert oversized[0].text == sentences[1]
    check_invariants(sentences, chunks, 200, 40)


def test_long_boundary_sentence_is_not_repeated_as_overlap():
    sentences = _sentences([80, 110, 80])
    chunks = chunk_sentences(sentences, max_words=200, overlap_words=40)
    check_invariants(sentences, chunks, 200, 40)
    assert chunks[1].overlap_sentences == 0     # 110 > 200 // 2


def test_single_sentence_bigger_than_overlap_is_still_carried():
    sentences = _sentences([60, 60, 60, 60])
    chunks = chunk_sentences(sentences, max_words=200, overlap_words=40)
    assert chunks[1].overlap_words == 60        # at least one sentence carried
    check_invariants(sentences, chunks, 200, 40)


def test_short_text_is_one_chunk():
    chunks = chunk_sentences(["Only one."], 200, 40)
    assert len(chunks) == 1 and chunks[0].text == "Only one."


def test_empty_and_blank_sentences():
    assert chunk_sentences([], 200, 40) == []
    assert chunk_sentences(["", "  "], 200, 40) == []


@pytest.mark.parametrize("max_words, overlap", [(0, 0), (-5, 0), (100, 100), (100, -1)])
def test_invalid_settings(max_words, overlap):
    with pytest.raises(ValueError):
        chunk_sentences(["A."], max_words, overlap)


def test_deterministic():
    sentences = _sentences([7, 13, 2, 40, 9, 9, 30])
    assert chunk_sentences(sentences, 50, 10) == chunk_sentences(list(sentences), 50, 10)


def test_randomised_invariants():
    """500 random documents, including empty, tiny and very long sentences."""
    rng = random.Random(2026)
    for _ in range(500):
        lengths = [rng.choice([1, 2, 5, 12, 25, 40, 80, 150, 230])
                   for _ in range(rng.randint(0, 60))]
        max_words = rng.choice([20, 50, 100, 200])
        overlap = rng.choice([0, 1, max_words // 5, max_words // 2, max_words - 1])
        sentences = _sentences(lengths)
        check_invariants(sentences, chunk_sentences(sentences, max_words, overlap),
                         max_words, overlap)
