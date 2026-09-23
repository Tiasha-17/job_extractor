"""
A small accuracy evaluation: run the extractor over the sample postings
and check its output against hand-labeled correct answers.

The score covers four fields in three synthetic postings, not overall accuracy.

Usage (from the project's root folder):
    python eval/evaluate.py
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from extractor import extract_posting  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
LABELS_PATH = os.path.join(HERE, "labels.json")
POSTINGS_DIR = os.path.join(os.path.dirname(HERE), "sample_postings")


def main():
    with open(LABELS_PATH) as f:
        labels = json.load(f)

    total_fields = 0
    correct_fields = 0

    for filename, expected in labels.items():
        path = os.path.join(POSTINGS_DIR, filename)
        with open(path) as f:
            raw_text = f.read()

        predicted = extract_posting(raw_text)
        print(f"\n{filename}")
        for field, expected_value in expected.items():
            actual_value = predicted.get(field)
            match = actual_value == expected_value
            total_fields += 1
            correct_fields += int(match)
            status = "OK  " if match else "MISS"
            print(f"  [{status}] {field}: expected={expected_value!r} actual={actual_value!r}")

    accuracy = correct_fields / total_fields if total_fields else 0
    print(f"\nField-level accuracy: {correct_fields}/{total_fields} = {accuracy:.0%}")


if __name__ == "__main__":
    main()
