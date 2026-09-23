# Setup and evaluation guide

[Back to project overview](../README.md)

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

