# Text Chunking and Cleaning Pipeline

**Mentroid ML Team: Practical Task 2**

**Author:** K Daniel Joseph · dannyjoseph3007@gmail.com · [github.com/d3005](https://github.com/d3005)

A dependency-free Python pipeline that takes a messy Project Gutenberg book chapter and produces clean text plus **overlapping chunks of at most 200 words that never cut a sentence in half**. Chunks of this kind are what retrieval-augmented generation (RAG) and embedding pipelines need.

---

## 1. Problem statement

Take a long, messy text file, here a public-domain chapter downloaded from Project Gutenberg, and write a Python script that:

1. strips out special characters,
2. normalises whitespace,
3. splits the text into **overlapping 200-word chunks** without cutting sentences mid-way.

## 2. Input

*The Adventures of Sherlock Holmes* by Arthur Conan Doyle, Project Gutenberg eBook **#1661**, chapter I, **"A Scandal in Bohemia"** → [`data/raw/sherlock_holmes_ch1_a_scandal_in_bohemia.txt`](data/raw/sherlock_holmes_ch1_a_scandal_in_bohemia.txt)

The file is kept exactly as Gutenberg serves it, mess included:

- Gutenberg's licence **header and footer** (about 19 KB of non-book text)
- Windows **CRLF** line endings and **hard-wrapped lines** at about 70 characters
- section headings such as `ADVENTURE I. A SCANDAL IN BOHEMIA`, `I.`, `II.`, `III.`
- `--` used as a dash, `_underscores_` for italics, and nested quotations
- abbreviations that trip up naive sentence splitters: `Mr.`, `Mrs.`, `Dr.`, `St.`

This chapter was chosen because it is full of these cases. It can be re-downloaded, or another book used, with [`scripts/fetch_chapter.py`](scripts/fetch_chapter.py).

## 3. Approach

```
raw .txt ─► strip Gutenberg ─► clean ─► split into ─► pack whole sentences ─► cleaned.txt
            header/footer      text     sentences     into 200-word chunks    chunks.jsonl
                                                      with overlap            stats.json
```

Each stage is a small, separately tested module in [`textpipe/`](textpipe):

| Stage | Module | What it does |
|---|---|---|
| Boilerplate | `gutenberg.py` | Keeps only the text between `*** START OF … ***` and `*** END OF … ***`. Matching is loose enough for old and new marker wordings. If no marker is found, the text is left unchanged. |
| Cleaning | `cleaning.py` | ① Unicode NFKC; smart quotes → `'` `"`; en/em dashes and `--` → ` - `; `…` → `...`. ② Split into paragraphs on blank lines (CRLF-safe). ③ Drop headings: section numbers (`I.`, `XII`, `Chapter 3`), short ALL-CAPS titles and `[Illustration]` tags. ④ **Strip special characters**: everything except letters, digits, whitespace and `. , ! ? ; : ' " - ( ) & %`. ⑤ **Normalise whitespace**: unwrap hard line breaks, collapse whitespace runs to one space, remove spaces before punctuation. |
| Sentences | `sentences.py` | Rule-based splitter. A boundary falls after `.` `!` `?` (plus any closing quote or bracket) **only** when the next token starts with a capital letter, a digit or an opening quote. Abbreviations (`Mr.`, `Dr.`, `St.`, `e.g.`), single initials (`A. Conan Doyle`, but never the pronoun `I.`) and number abbreviations (`No. 221`) are not boundaries. Neither is `"Who is it?" said he`. Sentences never cross paragraphs. |
| Chunking | `chunking.py` | Greedy packing of **whole sentences** up to `max_words` (200). When a chunk is full, its trailing sentences, up to `overlap_words` (40), are repeated at the start of the next chunk. |

### Key design decisions

- **Why keep some punctuation when the task says "strip special characters"?** Sentence punctuation is what makes "don't cut sentences" possible. Removing it would make sentence boundaries undetectable. Everything else that is not text, such as markup, symbols and brackets, is removed.
- **What "200-word chunks" means here.** 200 is a hard **maximum**, and chunks are packed as close to it as whole sentences allow. A chunk only goes over 200 words if a *single sentence* is longer than 200 words. That sentence becomes its own chunk with `oversized: true`, because cutting it would break the stated rule. This never happens in this chapter.
- **Overlap is sentence-aligned.** It is measured in words (target 40, about 20% of a chunk) but always consists of whole sentences, so overlapping text is never cut either. At least one sentence is always carried over, unless that single sentence is longer than half a chunk, in which case repeating it would make chunks mostly duplicates.
- **Word definition.** A word is a run of letters or digits, so `don't` and `well-known` each count as one word and a stand-alone `-` counts as none.
- **No third-party NLP dependencies.** I chose a rule-based splitter over spaCy or NLTK so the pipeline is deterministic, runs offline and installs instantly. Its accuracy on this chapter was checked by the tests (section 6).

## 4. Setup and run

Requires **Python 3.8+**. The pipeline uses only the standard library; `pytest` is needed only for the tests.

```bash
git clone https://github.com/d3005/mentroid-ml-task2-text-chunking-and-cleaning-pipeline-k.git
cd mentroid-ml-task2-text-chunking-and-cleaning-pipeline-k

python run_pipeline.py                     # uses the included chapter, writes output/
```

Options:

```bash
python run_pipeline.py path/to/book.txt --max-words 200 --overlap-words 40 -o output --preview 2
```

Download a different chapter (tries gutenberg.org first, then the GITenberg mirror on GitHub):

```bash
python scripts/fetch_chapter.py --book 1342 --start "Chapter 1" --end "Chapter 2" \
    --out data/raw/pride_and_prejudice_ch1.txt
```

Use it as a library:

```python
from textpipe import run_file
result = run_file("data/raw/sherlock_holmes_ch1_a_scandal_in_bohemia.txt",
                  max_words=200, overlap_words=40)
for chunk in result.chunks[:3]:
    print(chunk.chunk_id, chunk.word_count, chunk.text[:80])
```

Run the tests:

```bash
pip install -r requirements-dev.txt
python -m pytest
```

### Outputs ([`output/`](output))

| File | Contents |
|---|---|
| `cleaned.txt` | Clean text, one paragraph per block, blank line between paragraphs |
| `chunks.jsonl` | One JSON object per chunk: `chunk_id`, `text`, `word_count`, `sentence_start`, `sentence_end`, `overlap_words`, `overlap_sentences`, `oversized` |
| `stats.json` | Input, cleaning and chunk statistics |

## 5. Results

Run on "A Scandal in Bohemia" with `max_words=200`, `overlap_words=40`:

```
Input        data/raw/sherlock_holmes_ch1_a_scandal_in_bohemia.txt
Boilerplate  header=True footer=True removed 19,371 chars
Cleaned      8,533 words, 258 paragraphs, 657 sentences
Chunks       55 (words min 73, mean 187.7, max 200; oversized 0)
Overlap      mean 33.2 words; 0 boundaries without overlap
```

| Metric | Value |
|---|---|
| Raw file | 65,862 chars / 11,663 words (including Gutenberg licence) |
| Boilerplate removed | 19,371 chars (header + footer), plus 4 headings (`ADVENTURE I. …`, `I.`, `II.`, `III.`) |
| Cleaned text | 8,533 words · 258 paragraphs · 657 sentences |
| Chunks | **55** |
| Words per chunk | min 73 · mean 187.7 · median 192 · **max 200** |
| Chunks over 200 words | **0** |
| Sentences cut mid-way | **0** (each chunk is verified to be a run of whole sentences) |
| Mean overlap | 33.2 words; every one of the 54 boundaries overlaps |

Chunk-size distribution: 47 of 55 chunks hold 180–200 words. The 73-word chunk is the last one, which holds whatever text is left at the end.

**Overlap example.** Chunk 4 ends and chunk 5 begins with the same whole sentences (22 words):

> chunk 4: …and that you have a most clumsy and careless servant girl?" **"My dear Holmes," said I, "this is too much. You would certainly have been burned, had you lived a few centuries ago.**
>
> chunk 5: **"My dear Holmes," said I, "this is too much. You would certainly have been burned, had you lived a few centuries ago.** It is true that I had a country walk on Thursday…

The settings are easy to change. With `--max-words 100 --overlap-words 20` the chapter gives 120 chunks (max 100 words). With `--max-words 300 --overlap-words 60` it gives 37 chunks (max 300).

## 6. Tests

`python -m pytest` runs **70 tests in under a second**. No network is needed.

| File | Covers |
|---|---|
| `test_gutenberg.py` | old and new marker wordings, plain old-style footer, no markers, bad input |
| `test_cleaning.py` | CRLF and hard wraps, smart quotes and dashes, every removed special character, kept punctuation, accented letters, heading vs. prose (`"WHAT ARE YOU DOING?"` is prose), empty input |
| `test_sentences.py` | 15 tricky cases: `Mr.`/`Dr.`/`St.`, initials, the pronoun `I.`, `No. 221`, `e.g.`, `"Who is it?" said he`, decimals, ellipses, brackets; text preserved exactly |
| `test_chunking.py` | packing, multi-sentence overlap, zero overlap, oversized sentences, invalid settings, determinism, and a **randomised check of every guarantee on 500 generated documents** |
| `test_pipeline.py` | the real chapter end to end (no boilerplate, no special characters, no chunk over 200 words, every chunk whole sentences, every boundary overlapping, no abbreviation mis-splits), output files, and the command-line interface |

## 7. Assumptions and limitations

- **English prose.** The sentence rules and abbreviation list are for English. Text in other languages is cleaned correctly, but sentence splitting would need its own rules.
- **Rule-based splitting is not perfect.** An abbreviation missing from the list, or a sentence that starts with a lower-case word (for example `iPhone sales rose.`), can merge two sentences. A merge only makes a chunk slightly smaller; it can never cut a sentence.
- **Multi-sentence quotations are split inside the quote.** `"No. I disagree."` becomes `"No.` and `I disagree."`. Chunk text is unaffected because consecutive sentences are re-joined.
- **Heading detection is heuristic.** It looks for short ALL-CAPS lines and section numbers standing as their own paragraph. A one-line all-caps sentence ending in `.` could be dropped. Pass `drop_headings=False` to `clean_paragraphs` to keep everything.
- **Words are counted, not tokens.** If chunks feed an LLM with a token limit, 200 words is roughly 260–300 tokens; adjust `--max-words` to fit.
- **The last chunk can be short**, here 73 words, because it holds the remainder of the text.
- The input file was saved from the GITenberg mirror on GitHub of the identical Gutenberg text, because gutenberg.org was unreachable from my build environment. `fetch_chapter.py` tries gutenberg.org first.

## 8. Project structure

```
├── run_pipeline.py          # command-line entry point
├── textpipe/
│   ├── gutenberg.py         # licence header/footer removal
│   ├── cleaning.py          # special characters, whitespace, headings
│   ├── sentences.py         # rule-based sentence splitter
│   ├── chunking.py          # overlapping whole-sentence chunks
│   └── pipeline.py          # ties the stages together, writes outputs
├── scripts/fetch_chapter.py # downloads a chapter from Project Gutenberg
├── data/raw/                # input chapter, unmodified
├── output/                  # cleaned.txt, chunks.jsonl, stats.json
└── tests/                   # 70 pytest tests
```

---

Source text: *The Adventures of Sherlock Holmes* by Arthur Conan Doyle, from Project Gutenberg (public domain in the USA). Gutenberg's licence text is included unmodified in the raw input file.
