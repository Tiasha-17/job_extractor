# Job-Description Structured Extractor

A small local portfolio app that extracts job details and explicit UK visa
sponsorship signals from pasted postings using Ollama `qwen2.5:7b-instruct`.
Streamlit displays the result and SQLite stores it for review. No API key is needed.

## Setup and run

Use Python 3.12 (the version verified for this project). Install Ollama from
[ollama.com](https://ollama.com), open the Ollama application, and download the model:

```bash
ollama pull qwen2.5:7b-instruct
ollama list
```

Keep Ollama running. If you do not use its desktop application, run `ollama serve`
in a separate terminal. Do not start a second server if one already runs.

From the project directory:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python extractor.py
python -m streamlit run app.py
```

Open the local URL printed by Streamlit. Paste a posting and click Extract.
Successful extractions are saved automatically. To extract a file instead:

```bash
python cli.py sample_postings/posting_1_data_analyst_sponsorship.txt
```

If the app cannot connect, open Ollama or run `ollama serve`. If the model is missing,
run the pull command above. Requests have a 120-second network timeout; slow hardware
or model loading can require retrying. The app keeps the latest successful result
visible even if a database save fails.

## Architecture

```text
Streamlit app / CLI / evaluation scripts
                  |
          extract_posting(text)
                  |
       Ollama + qwen2.5:7b-instruct
       JSON schema, temperature=0
                  |
       JSON parse + schema validation
                  |
        Python dictionary
          /             \
 SQLite (app/CLI)     comparison report (evaluation)
```

| File | Responsibility |
| --- | --- |
| `schema.py` | Existing extraction fields, types, enums and required keys. |
| `extractor.py` | Shared prompt/model call, timeout, output validation, actionable errors. |
| `storage.py` | SQLite initialization, duplicate-aware saves, history reads. |
| `app.py` | Paste/extract interface, persistent last result, saved history and error messages. |
| `cli.py` | Extract one text file and save it. |
| `eval/evaluate.py` | Original three-posting synthetic evaluation. |
| `eval/real_world.py` | Prepare human labels and compare real postings without saving to SQLite. |
| `tests/test_workflows.py` | Offline regression tests, including Streamlit interaction tests. |

The schema is unchanged. The prompt now explicitly discourages inferring unstated
employment types and working arrangements. Schema validation checks structure;
it does not establish that a model's claims are factually correct. SQLite lives beside `storage.py`, independent of the terminal's working directory.

## Current test results (23 September 2026)

- Previously reported by the project owner: extractor smoke test and all three
  sample postings worked; synthetic evaluation was **12/12 = 100%**.
- This maintenance run: **7/7 offline regression tests passed**.
- Follow-up live verification: Ollama was reachable, the extractor smoke test passed,
  and the synthetic evaluation passed **12/12 = 100%** across all three samples.
  The seven offline regression tests also passed again.
- Baseline, five real user-supplied postings: **12/20 (60%) exact agreement with AI-assisted
  reference labels**, with zero extraction failures. This is not an independent
  human-labelled accuracy result. All five texts omit sponsorship wording.
  See [evaluation notes](docs/evaluation.md) for interpretation. Raw real adverts
  and local reports are excluded from this repository.

- After a targeted prompt clarification: **14/20 (70%)** on the same five postings,
  with zero extraction failures. Employment-type agreement improved from 1/5 to 2/5;
  working-arrangement agreement improved from 3/5 to 4/5. Three unsupported Full-time
  predictions remain. Seven regression tests and the 12/12 synthetic evaluation
  passed again. This is a same-set tuning comparison, not independent test accuracy.
  See [evaluation notes](docs/evaluation.md) for details and reproducibility limits.

Run the checks:

```bash
python -m unittest discover -s tests -v
python extractor.py
python eval/evaluate.py
```

The synthetic score covers only seniority, employment type, remote policy and
sponsorship signal: four fields across three invented examples. It does not measure
all extracted fields and is not evidence of 100% real-world accuracy.

## Manually evaluate 5–10 real postings

1. Create `eval/real/` and save 5–10 complete real postings there as UTF-8 `.txt`
   files, one posting per file. Include varied roles, remote policies, and explicit,
   negative and absent sponsorship wording. Keep source URLs and collection dates
   in a separate notes file. Avoid duplicate postings in this evaluation set.
2. Create the label template:

   ```bash
   python eval/real_world.py prepare eval/real
   ```

3. Open `eval/real/labels.json`. Read the original postings **before looking at
   model output**. Replace every `null` with your own label. The four categorical
   fields use these exact values:

   | Field | Allowed values |
   | --- | --- |
   | seniority_level | Internship; Entry-level/Junior; Mid-level; Senior; Lead/Staff; Manager/Director; Unknown |
   | employment_type | Full-time; Part-time; Contract; Internship; Not specified |
   | remote_policy | Remote; Hybrid; Onsite; Not specified |
   | sponsorship_signal | Sponsorship offered; No sponsorship / must have right to work; Not mentioned |

   Copy the sponsorship sentence verbatim into `sponsorship_evidence_quote`.
   For `Not mentioned`, use `""`. Do not infer sponsorship from the employer's
   reputation. Record ambiguous decisions in your notes and apply a consistent
   interpretation. Seniority can require judgement under the existing schema.

4. Run with Ollama available:

   ```bash
   python eval/real_world.py run eval/real
   ```

   The script validates all labels first, prints field matches, and writes a new
   timestamped `report-*.json` beside the labels. It never writes to SQLite or
   overwrites labels or reports. Each report contains human labels, predictions,
   mismatches, per-field correct counts and extraction errors. The denominator is
   all four labels for all postings, including failed extractions. Exit code 0 means
   all four fields matched; 1 means mismatches or extraction failures; 2 means setup
   errors. Evidence diagnostics are separate from the four-field score.

5. Review `evidence_exact_match` and `evidence_grounded` in each result. An alternative
   valid sentence may fail exact match; a verbatim quote can still be irrelevant.
   Human review remains necessary. Manually inspect skills, salaries and other
   fields too: the numeric score does not cover them.

The prepare command refuses to overwrite existing labels. To add a posting later,
add its filename and five labels manually, or use a new evaluation folder. Use a
new held-out set after tuning; do not present performance on tuned examples as an
independent test. Five to ten examples are an exploratory check, not a benchmark.

## Duplicate handling

Inspection found five saved rows and one exact duplicate group. Existing rows are
preserved. New saves compare the full text after trimming leading/trailing whitespace
and return the earliest matching ID. The first extraction and source note are retained.
Different internal whitespace, changed wording and different postings remain distinct.

`BEGIN IMMEDIATE` makes the check and insert a single serialized write transaction,
so two app/CLI saves cannot race through this code. This small-project solution scans
stored text and requires no database migration. Direct SQL inserts can bypass it.
For a larger dataset, use a normalized-text hash with a unique index and an explicit,
reviewed migration strategy for legacy duplicates. No legacy records were deleted.

## Limitations and interview explanation

- Local inference depends on Ollama being running and enough memory being available.
  This is a local demo; hosting Streamlit alone does not provide the local model.
- Structured output reduces format errors; it does not prevent incorrect extraction.
  Temperature zero helps consistency but does not guarantee identical results.
- Runtime validation protects storage and the UI from malformed output without
  changing what the model is asked to extract.
- Separate human labels and saved predictions make errors inspectable and avoid
  treating the model's own output as ground truth.
- SQLite and full-history reads suit a small personal tool; large-scale use would
  need pagination, indexing and stronger duplicate constraints.
- Raw postings are stored locally in plaintext. Review permissions and source terms
  before publishing any collected text. The database and real evaluation folder
  are ignored by Git by default.
- Dependencies are not pinned; record installed versions when comparing runs.
  CLI and original synthetic evaluation still surface exceptions in the terminal;
  the Streamlit interface provides user-facing recovery messages.

The real-posting baseline identified unsupported Full-time predictions in four
postings. A targeted prompt clarification improved same-set agreement from 60% to
70%, but three such guesses remain. The schema is unchanged. Original and revised
prompts and reports are retained locally; independent real-posting validation is
still needed.
