"""
The one function that talks to the model. Everything else in this project
(the CLI, the Streamlit app, the eval script) calls extract_posting() and
gets back a plain Python dict that always matches schema.py.

Runs entirely on your own Mac via Ollama — no API key, no account, no cost.
Ollama must be running in the background (open the Ollama app once, or run
`ollama serve`) and the model below must already be pulled — see the setup
guide for both steps.
"""

import json

import ollama
import httpx
from jsonschema import validate, ValidationError

from schema import EXTRACTION_SCHEMA

# Swap this for "llama3.2:3b" if qwen2.5:7b-instruct feels slow or your Mac
# struggles with it (see the setup guide's model-choice note).
MODEL = "qwen2.5:7b-instruct"

SYSTEM_PROMPT = (
    "You extract structured facts from job postings for a job seeker who "
    "needs visa sponsorship to work in the UK. Read the posting carefully. "
    "If the posting does not explicitly say whether it offers sponsorship or "
    "requires right to work, set sponsorship_signal to 'Not mentioned' — "
    "never guess or infer this from the company type or role. When you do "
    "find a sponsorship-related sentence, copy it into sponsorship_evidence_quote "
    "exactly as written, do not paraphrase it. "
    "For employment_type, use only an employment type explicitly stated in the "
    "posting. If none is stated, return 'Not specified'; never assume Full-time "
    "from the title, responsibilities, benefits, or experience requirements. "
    "For remote_policy, use only an explicitly stated Remote, Hybrid, or Onsite "
    "working arrangement. If none is stated, return 'Not specified'. A city, "
    "office address, onsite parking, office amenities, or flexible working alone "
    "does not establish a working arrangement. "
    "Respond with only the JSON object, "
    "matching this schema exactly:\n" + json.dumps(EXTRACTION_SCHEMA)
)


class ExtractionError(RuntimeError):
    """An extraction failure with an actionable message for the user."""


def extract_posting(raw_text: str) -> dict:
    """Extract and validate one posting; never return invalid output."""
    if not raw_text.strip():
        raise ExtractionError("Paste a non-empty job posting first.")
    try:
        response = ollama.Client(timeout=120).chat(
            model=MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"Job posting:\n\n{raw_text.strip()}"},
            ],
            format=EXTRACTION_SCHEMA,
            options={"temperature": 0},
        )
        result = json.loads(response.message.content)
        validate(result, EXTRACTION_SCHEMA)
        return result
    except (ConnectionError, httpx.ConnectError) as exc:
        raise ExtractionError("Cannot connect to Ollama. Open the Ollama app or run `ollama serve`, then try again.") from exc
    except httpx.TimeoutException as exc:
        raise ExtractionError("Ollama timed out after 120 seconds. Try again when the model has loaded, or use a shorter posting.") from exc
    except ollama.ResponseError as exc:
        message = (f"Model unavailable. Run `ollama pull {MODEL}`, then try again."
                   if exc.status_code == 404 else f"Ollama returned an error (HTTP {exc.status_code}). Check the Ollama service and retry.")
        raise ExtractionError(message) from exc
    except (json.JSONDecodeError, ValidationError, TypeError, AttributeError) as exc:
        raise ExtractionError("The model returned invalid structured output. Nothing was saved; please retry.") from exc
    except httpx.HTTPError as exc:
        raise ExtractionError("Communication with Ollama failed. Check the service and retry.") from exc


if __name__ == "__main__":
    # Quick manual smoke test: python extractor.py
    sample = """
    Data Analyst — Acme Retail Ltd, London (Hybrid)
    We're looking for a Data Analyst with 2+ years' experience in SQL and
    Power BI. Python is a bonus. Full-time, £32,000-£38,000. We are able to
    sponsor a Skilled Worker visa for the right candidate.
    """
    result = extract_posting(sample)
    print(json.dumps(result, indent=2))
