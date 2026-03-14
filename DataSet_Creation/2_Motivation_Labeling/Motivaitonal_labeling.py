#!/usr/bin/env python3

import os
import sys
import json
import time
import re
import requests
from typing import Optional

# -------------------------
# CONFIG
# -------------------------

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_FILE = os.path.join(BASE_DIR, "../1_Original_DataSet/emails_base.json")
OUTPUT_FILE = os.path.join(BASE_DIR, "emails_labeled_gemini.json")

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
API_KEY = os.getenv("OPENROUTER_API_KEY")

MODEL_ID = "google/gemini-2.5-flash"
TEMPERATURE = 0
TIMEOUT = 120
SLEEP_SEC = 0.3

VALID_MOTIVATIONS = {
    "Follow the link",
    "Open attachment",
    "Reply",
    "Unknown"
}

if not API_KEY:
    sys.exit("ERROR: Please export OPENROUTER_API_KEY first")

# -------------------------
# PROMPT
# -------------------------

def normalize_field(field):
    if not field:
        return "None"

    if isinstance(field, list):
        if len(field) == 0:
            return "None"
        return "\n".join(f"- {item}" for item in field)

    if isinstance(field, str):
        return f"- {field}"

    return "None"


def build_prompt(subject, body, url, file):

    url_str = normalize_field(url)
    file_str = normalize_field(file)

    return f"""
You are an email security analyst.

This dataset contains phishing, spam, and legitimate emails.

Your task is to classify the PRIMARY explicitly requested user action.

The "motivation" field MUST be exactly ONE of:
- "Follow the link"
- "Open attachment"
- "Reply"
- "Unknown"

DEFINITION:
Classify based on the main action the sender explicitly wants the recipient to perform.

DECISION RULES (apply in order):

1. If the email explicitly instructs the recipient to open, download, review, or access an attached file 
   OR if an attachment is present and clearly referenced: "Open attachment"

2. If the email explicitly instructs the recipient to click, visit, confirm, verify, log in, submit, view, 
   or access something via a link: "Follow the link"

IMPORTANT:
- The mere presence of a URL is NOT sufficient.
- Passive reference links (citations, footer links, unsubscribe links, sponsor banners) do NOT count unless clearly emphasized as the main action.

3. If the email explicitly asks the recipient to reply, respond, send information, 
   or submit content via email: "Reply"

4. If no clear action is requested: "Unknown"

Respond ONLY in strict JSON format:
{{"motivation": "Follow the link"}}

Email:
Subject: {subject}
Body: {body}

URL Field:
{url_str}

Attachment Field:
{file_str}
""".strip()

# -------------------------
# API CALL
# -------------------------

def call_model(messages):

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": MODEL_ID,
        "messages": messages,
        "temperature": TEMPERATURE,
        "max_tokens": 128,
        "response_format": {"type": "json_object"},
    }

    r = requests.post(
        OPENROUTER_URL,
        headers=headers,
        json=payload,
        timeout=TIMEOUT
    )

    r.raise_for_status()
    data = r.json()
    return data["choices"][0]["message"]["content"]

# -------------------------
# JSON PARSER
# -------------------------

def try_parse_json(s: str) -> Optional[dict]:
    try:
        return json.loads(s)
    except:
        pass

    match = re.search(r"\{[\s\S]*\}", s)
    if match:
        try:
            return json.loads(match.group(0))
        except:
            return None
    return None

# -------------------------
# LOAD DATASET
# -------------------------

with open(INPUT_FILE, "r", encoding="utf-8") as f:
    dataset = json.load(f)

print(f"Loaded {len(dataset)} emails")

# If output file exists → resume from it
if os.path.exists(OUTPUT_FILE):
    print("Resuming from existing labeled file...")
    with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
        dataset = json.load(f)

# -------------------------
# LABELING LOOP
# -------------------------

for i, email in enumerate(dataset):

    # Skip already labeled
    if email.get("Motivation_Gemini"):
        continue

    subject = email.get("Subject", "") or ""
    body = email.get("Body", "") or ""
    url = email.get("URL", "") or ""
    file = email.get("File", "") or ""
    email_no = email.get("No.", "?")

    prompt = build_prompt(subject, body, url, file)

    messages = [
        {"role": "system", "content": "Respond ONLY in valid JSON."},
        {"role": "user", "content": prompt},
    ]

    try:
        raw = call_model(messages)
        parsed = try_parse_json(raw)

        if parsed and parsed.get("motivation") in VALID_MOTIVATIONS:
            label = parsed["motivation"]
        else:
            label = "Unknown"

    except Exception as e:
        print(f"Error on email {email_no}: {e}")
        label = "Unknown"

    email["Motivation_Gemini"] = label

    print(f"[{i+1}/{len(dataset)}] Email {email_no}: {label}")

    # SAVE AFTER EVERY EMAIL (CRASH SAFE)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(dataset, f, ensure_ascii=False, indent=2)

    time.sleep(SLEEP_SEC)

print("Finished labeling entire dataset safely.")
