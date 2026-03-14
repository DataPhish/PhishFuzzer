import json
import re
from collections import Counter
import sys

MANUAL_TARGET = 100
NON_MANUAL_TARGET = 1000


def normalize_source(source):
    if not source:
        return "Unknown"

    # Remove Line / Email suffix
    source = re.sub(r"\b(Line|Email)\s+\d+\b", "", source, flags=re.IGNORECASE)
    return source.strip()


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def normalize_records(data):
    if isinstance(data, list):
        return data
    elif isinstance(data, dict):
        return [data]
    else:
        print("Invalid JSON structure")
        sys.exit(1)


def compute_balance(records):
    manual_counts = Counter()
    non_manual_counts = Counter()

    for record in records:
        if not isinstance(record, dict):
            continue

        source = normalize_source(record.get("Source", "Unknown"))
        record_type = record.get("Type", "Unknown")

        if source.lower() == "manual":
            manual_counts[record_type] += 1
        else:
            non_manual_counts[record_type] += 1

    return manual_counts, non_manual_counts


def print_balance(manual_counts, non_manual_counts):
    all_types = set(manual_counts.keys()) | set(non_manual_counts.keys())

    print("\n=== BALANCE REPORT (Manual=100, Non-Manual=1000) ===\n")

    for t in sorted(all_types):
        manual = manual_counts[t]
        non_manual = non_manual_counts[t]

        missing_manual = max(0, MANUAL_TARGET - manual)
        missing_non_manual = max(0, NON_MANUAL_TARGET - non_manual)

        print(f"Category: {t}")
        print(f"  Manual: {manual}")
        print(f"  Non-Manual: {non_manual}")
        print(f"  Missing Manual to reach {MANUAL_TARGET}: {missing_manual}")
        print(f"  Missing Non-Manual to reach {NON_MANUAL_TARGET}: {missing_non_manual}")
        print("")


def main(path):
    data = load_json(path)
    records = normalize_records(data)

    print(f"[OK] Loaded {len(records)} records")

    manual_counts, non_manual_counts = compute_balance(records)
    print_balance(manual_counts, non_manual_counts)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python balance_check.py <file.json>")
        sys.exit(1)

    main(sys.argv[1])
