# hunrhyme

Hungarian rhyme finder. Vowel-pattern matching against a corpus of Hungarian text (`full.txt`, `full_filtered.txt`). Two interchangeable surfaces:
- `app.py` — Streamlit app
- `index.html` — standalone client-side HTML version

## Critical rules

- **Hungarian vowel handling is the core of the project.** The vowel regex `[aáeéiíoóöőuúüűAÁEÉIÍOÓÖŐUÚÜŰ]` must include all accented forms. Don't simplify it to just `[aeiou]` — Hungarian rhyme depends on the long/short distinction (a vs á, e vs é, etc.).
- The two surfaces (`app.py` and `index.html`) should remain feature-parity. If you add a rhyme rule to one, mirror it in the other.
- `full.txt` and `full_filtered.txt` are the source corpora — don't accidentally regenerate or overwrite them without backing up.

## Stack & run

- Python: `streamlit run app.py` → http://localhost:8501
- Static: open `index.html` directly in a browser (no server, no build, all client-side)
- Tests: `python test_rhythm.py` (small smoke test for the rhythm-matching logic)

## Where things live

- `app.py` — Streamlit version with all the rhyme/rhythm logic
- `index.html` — standalone HTML version, vanilla JS, no dependencies
- `full.txt` — full Hungarian text corpus
- `full_filtered.txt` — cleaned/filtered version (the one the matcher uses)
- `test_rhythm.py` — minimal test for `check_rhythm()` logic

## Gotchas

- Hungarian-specific: every text input gets lowercased before vowel extraction. Don't add a step that strips accents — that destroys the rhyme signal.
- Word-vowel-count matching (`get_word_vowel_counts`) is the basis for rhythm matching. The "last N-1 words" comparison in `check_rhythm` is intentional; don't change it to "all words" without testing.
- No README in the repo. The code is the documentation — start there.
