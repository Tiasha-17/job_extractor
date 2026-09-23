"""
Command-line version: extract one posting from a text file and save it.

Usage:
    python cli.py sample_postings/posting_1_data_analyst_sponsorship.txt
"""

import json
import sys

from extractor import extract_posting
from storage import init_db, save_posting


def main():
    if len(sys.argv) < 2:
        print("Usage: python cli.py <path-to-posting.txt>")
        sys.exit(1)

    path = sys.argv[1]
    with open(path, "r", encoding="utf-8") as f:
        raw_text = f.read()

    print(f"Extracting from {path} ...")
    result = extract_posting(raw_text)
    print(json.dumps(result, indent=2))

    conn = init_db()
    save_posting(conn, raw_text, result, source_note=path)
    print("\nSaved to postings.db")


if __name__ == "__main__":
    main()
