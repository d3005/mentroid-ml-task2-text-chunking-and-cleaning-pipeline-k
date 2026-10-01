import json
import re
from pathlib import Path

import pytest

from run_pipeline import DEFAULT_INPUT, main
from textpipe.pipeline import run, run_file, write_outputs

ROOT = Path(__file__).resolve().parent.parent
INPUT = ROOT / DEFAULT_INPUT

needs_input = pytest.mark.skipif(not INPUT.is_file(),
                                 reason="run scripts/fetch_chapter.py first")


@pytest.fixture(scope="module")
def result():
    return run_file(INPUT, max_words=200, overlap_words=40)


@needs_input
def test_boilerplate_and_headings_are_gone(result):
    assert result.stats["input"]["gutenberg_header_found"]
    assert result.stats["input"]["gutenberg_footer_found"]
    lower = result.cleaned_text.lower()
    assert "project gutenberg" not in lower
    assert "adventure i." not in lower
    assert result.cleaned_text.startswith("To Sherlock Holmes she is always THE woman.")
    assert result.cleaned_text.rstrip().endswith("when he refers to her photograph, it is always under the honourable title of the woman.")


@needs_input
def test_cleaned_text_has_no_special_characters_or_messy_whitespace(result):
    assert not re.search(r"[^\w\s.,!?;:'\"()\-&%]|_", result.cleaned_text)
    assert "\r" not in result.cleaned_text
    assert "  " not in result.cleaned_text
    assert "\n\n\n" not in result.cleaned_text
    for paragraph in result.cleaned_text.split("\n\n"):
        assert "\n" not in paragraph


@needs_input
def test_real_chapter_chunks(result):
    chunks = result.chunks
    assert len(chunks) > 10
    assert all(c.word_count <= 200 for c in chunks)
    assert all(c.overlap_words > 0 for c in chunks[1:])
    for chunk in chunks:
        assert chunk.text == " ".join(result.sentences[chunk.sentence_start:chunk.sentence_end])
        assert re.search(r"[.!?:]['\")]*$", chunk.text) or chunk is chunks[-1] or \
            chunk.text.endswith(("-", '- "', ',')), chunk.text[-40:]


@needs_input
def test_no_known_abbreviation_mis_splits(result):
    for sentence in result.sentences:
        assert not re.search(r"\b(Mr|Mrs|Dr|St)\.$", sentence), sentence


def test_run_on_inline_text():
    raw = ("*** START OF THE PROJECT GUTENBERG EBOOK X ***\r\nCHAPTER I\r\n\r\n"
           + "Mr. Smith walked home.  It was late.\r\n" * 30
           + "*** END OF THE PROJECT GUTENBERG EBOOK X ***\r\nlicence")
    out = run(raw, max_words=40, overlap_words=10)
    assert out.stats["cleaned"]["sentences"] == 60
    assert all(c.word_count <= 40 for c in out.chunks)
    assert "CHAPTER" not in out.cleaned_text and "licence" not in out.cleaned_text


def test_write_outputs(tmp_path):
    out = run("One sentence here. Another one there.", max_words=5, overlap_words=2)
    paths = write_outputs(out, tmp_path)
    assert {p.name for p in paths} == {"cleaned.txt", "chunks.jsonl", "stats.json"}
    lines = (tmp_path / "chunks.jsonl").read_text().splitlines()
    assert [json.loads(line)["chunk_id"] for line in lines] == list(range(len(out.chunks)))
    assert json.loads((tmp_path / "stats.json").read_text())["chunks"]["count"] == len(out.chunks)


@needs_input
def test_cli(tmp_path, capsys, monkeypatch):
    monkeypatch.chdir(ROOT)
    assert main([str(DEFAULT_INPUT), "-o", str(tmp_path), "--preview", "1"]) == 0
    printed = capsys.readouterr().out
    assert "Chunks" in printed and "chunk 0" in printed
    assert (tmp_path / "chunks.jsonl").is_file()


def test_cli_missing_file(tmp_path):
    with pytest.raises(SystemExit):
        main([str(tmp_path / "missing.txt")])


def test_cli_bad_settings(tmp_path):
    source = tmp_path / "in.txt"
    source.write_text("Hello there.")
    with pytest.raises(SystemExit):
        main([str(source), "-o", str(tmp_path), "--max-words", "10", "--overlap-words", "10"])
