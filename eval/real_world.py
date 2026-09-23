"""Prepare human labels, then evaluate them without writing to postings.db."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from extractor import extract_posting, MODEL
from schema import EXTRACTION_SCHEMA

FIELDS = ('seniority_level', 'employment_type', 'remote_policy', 'sponsorship_signal')


def prepare(folder):
    files = sorted(folder.glob('*.txt'))
    if not files:
        raise ValueError('Add 5–10 UTF-8 posting .txt files to the folder first.')
    labels = {f.name: {**dict.fromkeys(FIELDS), 'sponsorship_evidence_quote': None} for f in files}
    path = folder / 'labels.json'
    with path.open('x', encoding='utf-8') as handle:
        json.dump(labels, handle, indent=2)
    print(f'Created {path}. Replace every null with your human label before evaluating.')


def load_cases(folder):
    labels = json.loads((folder / 'labels.json').read_text(encoding='utf-8'))
    if not isinstance(labels, dict) or not labels:
        raise ValueError('Labels must be a non-empty object keyed by posting filename.')
    cases = []
    for name, expected in labels.items():
        if Path(name).name != name or not name.endswith('.txt'):
            raise ValueError(f'Invalid posting filename: {name}')
        if not isinstance(expected, dict) or set(expected) != set(FIELDS) | {'sponsorship_evidence_quote'}:
            raise ValueError(f'{name}: label exactly the four categorical fields and evidence quote.')
        for field in FIELDS:
            if expected[field] not in EXTRACTION_SCHEMA['properties'][field]['enum']:
                raise ValueError(f'{name}: invalid or unfinished label for {field}')
        raw = (folder / name).read_text(encoding='utf-8')
        quote = expected['sponsorship_evidence_quote']
        if not raw.strip() or not isinstance(quote, str):
            raise ValueError(f'{name}: empty posting or unfinished evidence label')
        if expected['sponsorship_signal'] == 'Not mentioned':
            if quote != '':
                raise ValueError(f'{name}: use an empty quote for Not mentioned')
        elif not quote or quote not in raw:
            raise ValueError(f'{name}: evidence must be copied verbatim from the posting')
        cases.append((name, raw, expected))
    return cases


def evaluate(cases, extract=extract_posting):
    counts = {field: 0 for field in FIELDS}
    rows = []
    for name, raw, expected in cases:
        row = {'file': name, 'expected': expected}
        try:
            predicted = extract(raw)
            matches = {field: predicted.get(field) == expected[field] for field in FIELDS}
            for field, match in matches.items():
                counts[field] += int(match)
            quote = predicted.get('sponsorship_evidence_quote', '')
            row.update(predicted=predicted, matches=matches,
                       evidence_exact_match=quote == expected['sponsorship_evidence_quote'],
                       evidence_grounded=(quote == '' if predicted.get('sponsorship_signal') == 'Not mentioned'
                                          else bool(quote) and quote in raw))
        except Exception as exc:
            row['error'] = f'{type(exc).__name__}: {exc}'
        rows.append(row)
    total = len(cases) * len(FIELDS)
    return {'created_at': datetime.now(timezone.utc).isoformat(), 'model': MODEL,
            'postings': len(cases), 'failed_postings': sum('error' in r for r in rows),
            'correct_fields': sum(counts.values()), 'total_fields': total,
            'accuracy': sum(counts.values()) / total if total else 0,
            'per_field_correct': counts, 'results': rows}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['prepare', 'run'])
    parser.add_argument('folder', type=Path)
    args = parser.parse_args()
    try:
        if args.action == 'prepare':
            prepare(args.folder)
            return 0
        cases = load_cases(args.folder)  # Validate every human label before calling the model.
        if not 5 <= len(cases) <= 10:
            print('Note: aim for 5–10 real postings; this run uses', len(cases))
        report = evaluate(cases)
        path = args.folder / ('report-' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ') + '.json')
        with path.open('x', encoding='utf-8') as handle:
            json.dump(report, handle, indent=2, ensure_ascii=False)
        for row in report['results']:
            print(row['file'], row.get('error', row.get('matches')))
        print(f"Field accuracy: {report['correct_fields']}/{report['total_fields']} = {report['accuracy']:.1%}")
        print('Failed extractions (counted as incorrect):', report['failed_postings'])
        print('Report:', path)
        return int(report['failed_postings'] > 0 or report['correct_fields'] != report['total_fields'])
    except (ValueError, OSError) as exc:
        print(f'Evaluation setup error: {exc}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
