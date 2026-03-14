#!/usr/bin/env python3

import os
import sys
import json
import time
import requests
from collections import Counter
from copy import deepcopy

# ==========================
# CONFIG
# ==========================

INPUT_FILE = "emails_populating_benchmark.json"
OUTPUT_FILE = "emails_populated_benchmark_completion.json"

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
API_KEY = os.getenv("OPENROUTER_API_KEY")

if not API_KEY:
    sys.exit("ERROR: Please export OPENROUTER_API_KEY")

MODELS = [
    {"model_id": "anthropic/claude-3.5-sonnet", "name": "claude"},
    {"model_id": "openai/gpt-5.2-chat", "name": "gpt"},
    {"model_id": "google/gemini-2.5-flash", "name": "gemini"}
]

N_TRIES = 1
TEMPERATURE = 0.3
MAX_TOKENS = 300
TIMEOUT = 120
SLEEP_SEC = 0.5
DEBUG_PRINT_PROMPT = False

# ==========================
# BASE RULES
# ==========================

BASE_RULES = """
RULES:
1. If the Body contains explicit URL(s), extract and return those exact URL(s).
2. If the Body explicitly mentions attachment filename(s), extract and return those exact filename(s).
3. If the Body does NOT explicitly contain the URL or filename, but the email context clearly implies one,
   generate a realistic URL or filename consistent with the email content and Type.
4. Structural Enforcement by Motivation:
   - If Motivation = "Follow the link", a URL MUST NOT be null.
   - If Motivation = "Open attachment", a File MUST NOT be null.
   - If Motivation = "Reply" or "Unknown", structure must be inferred strictly from Body only.
5. If Motivation requires structure but none exists explicitly in the Body,
   generate a realistic artifact consistent with the email content and Type.
6. Do NOT generate both URL and File unless clearly implied.
7. Return null only when:
   - Motivation does not require structure
   - AND the Body does not imply structure.
8. Return strictly structured JSON only.
""".strip()

# ==========================
# PHISHING PROMPT
# ==========================

PHISHING_PROMPT = """
You are completing missing URL and File fields for phishing emails in a security dataset.

TASK:
Given an email (Subject, Body, Motivation), determine whether a realistic phishing email would include:A URL, An attachment file

URL RULE:
- Emails MUST NEVER use official domains.
- URLs should appear deceptive or impersonation-style.
- Avoid placeholder domains.

FILE RULE:
- Only add a File if clearly implied.
- Use realistic phishing-style names (e.g., invoice.pdf, secure_document.html, form.docx).

{BASE_RULES}

Respond ONLY in strict JSON format:
{{
  "URL": ["..."] or null,
  "File": ["..."] or null
}}

Email:
Subject: {subject}
Body: {body}
Motivation: {motivation}
""".strip()

# ==========================
# SPAM PROMPT
# ==========================

SPAM_PROMPT = """
You are completing missing URL and File fields for spam emails in a security dataset.

TASK:
Given an email (Subject, Body, Motivation), determine whether a realistic spam email would include: A URL, An attachment file

URL RULE:
- URLs must use real, official company domains.
- Only add a URL if promotional action is implied.

FILE RULE:
- Only add a File if implied.
- Use realistic marketing names (e.g., brochure.pdf, catalog.pdf).
- Do NOT generate malicious-looking file types.

{BASE_RULES}

Respond ONLY in strict JSON format:
{{
  "URL": ["..."] or null,
  "File": ["..."] or null
}}

Email:
Subject: {subject}
Body: {body}
Motivation: {motivation}
""".strip()

# ==========================
# VALID PROMPT
# ==========================

VALID_PROMPT = """
You are completing missing URL and File fields for legitimate emails in a security dataset.

TASK:
Given an email (Subject, Body, Motivation), determine whether a realistic legitimate email would include: A URL, An attachment file

URL RULE:
- URLs must be official and realistic.
- Only add a URL if clearly implied.

FILE RULE:
- Only add a File if explicitly referenced.
- Use professional filenames (e.g., agenda.pdf, report.docx, summary.xlsx).
- Do NOT invent attachments.

{BASE_RULES}

Respond ONLY in strict JSON format:
{{
  "URL": ["..."] or null,
  "File": ["..."] or null
}}

Email:
Subject: {subject}
Body: {body}
Motivation: {motivation}
""".strip()

# ==========================
# PROMPT BUILDER
# ==========================

def build_prompt(subject, body, motivation, email_type):

    if email_type == "Phishing":
        template = PHISHING_PROMPT
    elif email_type == "Spam":
        template = SPAM_PROMPT
    elif email_type == "Valid":
        template = VALID_PROMPT
    else:
        raise ValueError(f"Unknown Type: {email_type}")

    return template.format(
        subject=subject,
        body=body,
        motivation=motivation,
        BASE_RULES=BASE_RULES
    )

# ==========================
# API CALL
# ==========================

def call_model(model_id, messages):

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": model_id,
        "messages": messages,
        "temperature": TEMPERATURE,
        "max_tokens": MAX_TOKENS,
        "response_format": {"type": "json_object"},
    }

    r = requests.post(
        OPENROUTER_URL,
        headers=headers,
        json=payload,
        timeout=TIMEOUT
    )

    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"]

# ==========================
# Normalize
# ==========================

def normalize_value(v):
    """
    Normalize URL/File field to a comparable hashable form.
    """
    if v in ("Error", None, "null", ""):
        return None

    # If string → convert to single-item tuple
    if isinstance(v, str):
        return (v.strip(),)

    # If list → convert to sorted tuple
    if isinstance(v, list):
        return tuple(sorted(str(x).strip() for x in v))

    return None


def majority_vote(values):
    normalized = []

    for v in values:
        nv = normalize_value(v)
        if nv is not None:
            normalized.append(nv)

    if not normalized:
        return None, 0.0

    counts = Counter(normalized)
    majority, count = counts.most_common(1)[0]

    # Convert back to list for storage
    return list(majority), count / len(normalized)


# ==========================
# MAIN
# ==========================

if not os.path.exists(INPUT_FILE):
    sys.exit("Input file not found")

with open(INPUT_FILE, "r", encoding="utf-8") as f:
    data = json.load(f)

results = []

for idx, email in enumerate(data, 1):

    print(f"\nProcessing {idx}/{len(data)}")

    email_copy = deepcopy(email)

    subject = email.get("Subject", "") or ""
    body = email.get("Body", "") or ""
    motivation = email.get("Motivation", "Unknown")
    email_type = email.get("Type", "")

    prompt = build_prompt(subject, body, motivation, email_type)

    if DEBUG_PRINT_PROMPT:
        print("\n==============================")
        print(prompt)
        print("==============================\n")

    for model in MODELS:

        model_id = model["model_id"]
        model_name = model["name"]

        print(f"  → {model_name}")

        url_results = []
        file_results = []

        for i in range(1, N_TRIES + 1):

            try:
                messages = [
                    {"role": "system", "content": "Respond ONLY in valid JSON."},
                    {"role": "user", "content": prompt}
                ]

                raw = call_model(model_id, messages)
                parsed = json.loads(raw)

                url_val = parsed.get("URL")
                file_val = parsed.get("File")

                if url_val in ("", "null"):
                    url_val = None
                if file_val in ("", "null"):
                    file_val = None

                email_copy[f"URL_{model_name}_try{i}"] = url_val
                email_copy[f"File_{model_name}_try{i}"] = file_val

                url_results.append(url_val)
                file_results.append(file_val)

                print(f"    ✓ try{i}")

            except Exception:
                email_copy[f"URL_{model_name}_try{i}"] = "Error"
                email_copy[f"File_{model_name}_try{i}"] = "Error"
                url_results.append("Error")
                file_results.append("Error")
                print(f"    ✗ try{i}")

            time.sleep(SLEEP_SEC)

        url_majority, url_conf = majority_vote(url_results)
        file_majority, file_conf = majority_vote(file_results)

        email_copy[f"URL_{model_name}_majority"] = url_majority
        email_copy[f"URL_{model_name}_confidence"] = url_conf
        email_copy[f"File_{model_name}_majority"] = file_majority
        email_copy[f"File_{model_name}_confidence"] = file_conf

    results.append(email_copy)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

print("\nDone.")
