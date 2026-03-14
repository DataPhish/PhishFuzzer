#!/usr/bin/env python3

import os
import sys
import json
import time
import requests
import re
import unicodedata
from copy import deepcopy

# ==========================
# CONFIG
# ==========================

INPUT_FILE = "emails_labeled.json"
OUTPUT_FILE = "emails_populated_non_manual_gemini.json"

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
API_KEY = os.getenv("OPENROUTER_API_KEY")

if not API_KEY:
    sys.exit("ERROR: Please export OPENROUTER_API_KEY")

MODEL_ID = "google/gemini-2.5-flash"
MODEL_NAME = "gemini"

TEMPERATURE = 0.3
MAX_TOKENS = 400
TIMEOUT = 120
SLEEP_SEC = 0.5
MAX_RETRIES = 2

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
# HELPERS
# ==========================

def clean_text(text):
    """
    Remove problematic unicode and normalize.
    """
    if not text:
        return ""
    text = unicodedata.normalize("NFKC", text)
    text = text.replace("\u200b", "").replace("\u200c", "")
    return text


def safe_json_parse(raw):
    """
    Safely extract JSON object from model output.
    """
    try:
        return json.loads(raw)
    except:
        match = re.search(r"\{[\s\S]*\}", raw)
        if match:
            try:
                return json.loads(match.group(0))
            except:
                return None
    return None


def call_model(prompt):
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": MODEL_ID,
        "messages": [
            {"role": "system", "content": "Respond ONLY in valid JSON."},
            {"role": "user", "content": prompt}
        ],
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


def enforce_limits(urls):
    """
    Limit URL list to max 3.
    """
    if isinstance(urls, list):
        return urls[:3]
    return urls


# ==========================
# MAIN
# ==========================

if not os.path.exists(INPUT_FILE):
    sys.exit("Input file not found")

with open(INPUT_FILE, "r", encoding="utf-8") as f:
    data = json.load(f)

print(f"Loaded {len(data)} emails")

results = []

for idx, email in enumerate(data, 1):

    print(f"\nProcessing {idx}/{len(data)}")

    email_copy = deepcopy(email)

    # Skip manual entries
    if email.get("Source") == "Manual":
        print("  → Skipping (Manual)")
        results.append(email_copy)
        continue

    subject = clean_text(email.get("Subject", "") or "")
    body = clean_text(email.get("Body", "") or "")
    motivation = email.get("Motivation_Gemini", "Unknown")
    email_type = email.get("Type", "")

    if email_type == "Phishing":
        template = PHISHING_PROMPT
    elif email_type == "Spam":
        template = SPAM_PROMPT
    elif email_type == "Valid":
        template = VALID_PROMPT
    else:
        print("  → Unknown Type, skipping")
        results.append(email_copy)
        continue

    prompt = template.format(
        subject=subject,
        body=body,
        motivation=motivation,
        BASE_RULES=BASE_RULES
    )

    success = False

    for attempt in range(MAX_RETRIES):

        try:
            raw = call_model(prompt)
            parsed = safe_json_parse(raw)

            if not parsed:
                raise ValueError("Invalid JSON from model")

            url_val = parsed.get("URL")
            file_val = parsed.get("File")

            if url_val in ("", "null"):
                url_val = None
            if file_val in ("", "null"):
                file_val = None

            url_val = enforce_limits(url_val)

            email_copy["URL_gemini"] = url_val
            email_copy["File_gemini"] = file_val

            print("  ✓ Populated")
            success = True
            break

        except Exception as e:
            print(f"  ⚠ Retry {attempt+1}: {e}")
            time.sleep(1)

    if not success:
        print("  ✗ Failed after retries")
        email_copy["URL_gemini"] = None
        email_copy["File_gemini"] = None

    results.append(email_copy)

    # Save progressively
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    time.sleep(SLEEP_SEC)

print("\nDone.")
