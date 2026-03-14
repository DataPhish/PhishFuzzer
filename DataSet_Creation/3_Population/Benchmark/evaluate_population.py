#!/usr/bin/env python3

import json
import re

INPUT_FILE = "emails_populated_benchmark_completion.json"
MODELS = ["claude", "gpt", "gemini"]

# ==========================
# Helpers
# ==========================

def normalize_field(value):
    """
    Normalize URL/File fields:
    - None stays None
    - Empty string -> None
    - String -> [string]
    - List -> list
    """
    if value is None:
        return None

    if isinstance(value, str):
        value = value.strip()
        if value == "" or value.lower() == "null":
            return None
        return [value]

    if isinstance(value, list):
        if len(value) == 0:
            return None
        return value

    return None


def clean_url_string(u):
    """
    Remove wrapping characters like:
    [url], <url>, (url)
    """
    if not isinstance(u, str):
        return None

    cleaned = u.strip()
    cleaned = cleaned.strip("[]()<>")
    return cleaned.strip()


def has_valid_url(url_list):
    """
    Accept:
    - http://example.com
    - https://example.com
    - example.com
    - sub.domain.com

    Reject:
    - link
    - [link]
    - secure portal
    """

    if not url_list:
        return False

    pattern = re.compile(r"(https?://)?[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")

    for u in url_list:
        cleaned = clean_url_string(u)
        if cleaned and pattern.search(cleaned):
            return True

    return False


def get_true_url(email):
    """
    Handle both 'URL' and 'URL(s)' schema variants.
    """
    url = email.get("URL")

    if url is None:
        url = email.get("URL(s)")

    return normalize_field(url)


def get_true_file(email):
    return normalize_field(email.get("File"))


def get_predicted(email, model, field):
    return normalize_field(email.get(f"{field}_{model}_majority"))


# ==========================
# Main
# ==========================

with open(INPUT_FILE, "r", encoding="utf-8") as f:
    data = json.load(f)

print(f"Loaded {len(data)} emails")

for model in MODELS:

    print("\n====================================")
    print(f"EVALUATING: {model.upper()}")
    print("====================================")

    total = 0
    url_correct = 0
    file_correct = 0
    overall_correct = 0

    url_wrong_ids = []
    file_wrong_ids = []

    url_hallucinations = 0
    url_omissions = 0
    url_invalid = 0

    file_hallucinations = 0
    file_omissions = 0

    for email in data:

        email_id = email.get("No.")
        total += 1

        true_url = get_true_url(email)
        true_file = get_true_file(email)

        pred_url = get_predicted(email, model, "URL")
        pred_file = get_predicted(email, model, "File")

        # -------------------------
        # URL evaluation
        # -------------------------

        true_has_url = true_url is not None
        pred_has_url = pred_url is not None

        # Check validity of predicted URLs
        if pred_has_url and not has_valid_url(pred_url):
            url_invalid += 1
            url_wrong_ids.append(email_id)
            url_match = False
        else:
            url_match = (true_has_url == pred_has_url)

            if not url_match:
                url_wrong_ids.append(email_id)

                if not true_has_url and pred_has_url:
                    url_hallucinations += 1
                elif true_has_url and not pred_has_url:
                    url_omissions += 1

        if url_match:
            url_correct += 1

        # -------------------------
        # File evaluation
        # -------------------------

        true_has_file = true_file is not None
        pred_has_file = pred_file is not None

        file_match = (true_has_file == pred_has_file)

        if file_match:
            file_correct += 1
        else:
            file_wrong_ids.append(email_id)

            if not true_has_file and pred_has_file:
                file_hallucinations += 1
            elif true_has_file and not pred_has_file:
                file_omissions += 1

        # -------------------------
        # Overall structural correctness
        # -------------------------

        if url_match and file_match:
            overall_correct += 1

    # ==========================
    # Results
    # ==========================

    print(f"\nTotal Emails: {total}")

    print("\n--- URL ---")
    print(f"Accuracy: {url_correct / total:.4f}")
    print(f"Hallucinations: {url_hallucinations}")
    print(f"Omissions: {url_omissions}")
    print(f"Invalid Generated URLs: {url_invalid}")
    print(f"Wrong IDs ({len(url_wrong_ids)}):")
    print(url_wrong_ids)

    print("\n--- File ---")
    print(f"Accuracy: {file_correct / total:.4f}")
    print(f"Hallucinations: {file_hallucinations}")
    print(f"Omissions: {file_omissions}")
    print(f"Wrong IDs ({len(file_wrong_ids)}):")
    print(file_wrong_ids)

    print("\n--- Overall Structural Accuracy ---")
    print(f"{overall_correct / total:.4f}")
