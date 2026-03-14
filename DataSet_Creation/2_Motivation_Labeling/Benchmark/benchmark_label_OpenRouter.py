#!/usr/bin/env python3

import os
import sys
import json
import time
import re
import requests
from copy import deepcopy
from collections import Counter
from typing import Optional

# -------------------------
# Paths
# -------------------------

BASE_DIR = os.getcwd()

INPUT_FILE = os.path.join(BASE_DIR, "emails_label_benchmark.json")

RESULTS_DIR = os.path.join(BASE_DIR, "Benchmark_Results")
os.makedirs(RESULTS_DIR, exist_ok=True)

# -------------------------
# OpenRouter
# -------------------------

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
API_KEY = os.getenv("OPENROUTER_API_KEY")

if not API_KEY:
    sys.exit("ERROR: Please export OPENROUTER_API_KEY first")

# -------------------------
# MODELS
# -------------------------

MODELS = [
    {"model_id": "anthropic/claude-3.5-sonnet", "name": "claude"},
    {"model_id": "openai/gpt-5.2-chat", "name": "gpt"},
    {"model_id": "google/gemini-2.5-flash", "name": "gemini"},
    {"model_id": "qwen/qwen-2.5-7b-instruct", "name": "qwen"},
    {"model_id": "deepseek/deepseek-chat", "name": "deepseek"},
]

# -------------------------
# CONFIG
# -------------------------

N_TRIES_PER_EMAIL = 5
TEMPERATURE = 0   # Deterministic for benchmarking
SLEEP_SEC = 0.5
MAX_RETRIES = 4
TIMEOUT = 120
LIMIT = None  # Set to e.g. 50 for quick testing

VALID_MOTIVATIONS = {
    "Follow the link",
    "Open attachment",
    "Reply",
    "Unknown"
}

# -------------------------
# PROMPT
# -------------------------

def normalize_field(field):
    """
    Normalize URL or File field to a consistent bullet-list format.
    Always returns a string.
    """
    if not field:
        return "None"

    if isinstance(field, list):
        if len(field) == 0:
            return "None"
        return "\n".join(f"- {item}" for item in field)

    if isinstance(field, str):
        return f"- {field}"

    return "None"


def build_prompt(subject: str, body: str, url, file) -> str:

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
{{
  "motivation": "Follow the link"
}}

Email:
Subject: {subject}
Body: {body}

URL Field:
{url_str}

Attachment Field:
{file_str}
""".strip()


# -------------------------
# HELPERS
# -------------------------

def try_parse_json(s: str) -> Optional[dict]:
    try:
        return json.loads(s)
    except Exception:
        pass

    match = re.search(r"\{[\s\S]*\}", s)
    if match:
        try:
            return json.loads(match.group(0))
        except Exception:
            return None
    return None


def call_openrouter(model_id: str, messages: list) -> str:

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": model_id,
        "messages": messages,
        "temperature": TEMPERATURE,
        "max_tokens": 256,
        "response_format": {"type": "json_object"},
    }

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            r = requests.post(
                OPENROUTER_URL,
                headers=headers,
                json=payload,
                timeout=TIMEOUT
            )

            if r.status_code in (429, 503):
                time.sleep(min(10, attempt * 2))
                continue

            r.raise_for_status()
            data = r.json()
            return data["choices"][0]["message"]["content"]

        except Exception:
            if attempt == MAX_RETRIES:
                raise
            time.sleep(1.5 * attempt)


def majority_vote(email, base_key):
    votes = []
    for i in range(1, N_TRIES_PER_EMAIL + 1):
        key = f"{base_key}_try{i}"
        val = email.get(key)
        if val and val != "Error":
            votes.append(val)

    if not votes:
        return "Unknown", 0.0

    counts = Counter(votes)
    label, count = counts.most_common(1)[0]
    return label, count / len(votes)

# -------------------------
# LOAD DATASET
# -------------------------

if not os.path.exists(INPUT_FILE):
    sys.exit(f"ERROR: {INPUT_FILE} not found")

with open(INPUT_FILE, "r", encoding="utf-8") as f:
    base = json.load(f)

if LIMIT:
    base = base[:LIMIT]

print(f"Loaded {len(base)} emails")

# -------------------------
# RUNNER
# -------------------------

def run_model(model_cfg):

    model_id = model_cfg["model_id"]
    model_name = model_cfg["name"]

    print(f"\n=== Running {model_name} ===")

    records = deepcopy(base)

    outfile = os.path.join(RESULTS_DIR, f"{model_name}_results.json")

    for email in records:

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

        for i in range(1, N_TRIES_PER_EMAIL + 1):
            key = f"{model_name}_try{i}"

            try:
                raw = call_openrouter(model_id, messages).strip()
                parsed = try_parse_json(raw)

                if not parsed or "motivation" not in parsed:
                    email[key] = "Error"
                    print(f"[{model_name}] ✗ {email_no} try{i}")
                else:
                    label = parsed["motivation"]
                    if label not in VALID_MOTIVATIONS:
                        label = "Unknown"

                    email[key] = label
                    print(f"[{model_name}] ✓ {email_no} try{i}: {label}")

            except Exception as e:
                email[key] = "Error"
                print(f"[{model_name}] ✗ {email_no} try{i}: {e}")

            time.sleep(SLEEP_SEC)

        majority, confidence = majority_vote(email, model_name)
        email[f"{model_name}_majority"] = majority
        email[f"{model_name}_confidence"] = confidence

        with open(outfile, "w", encoding="utf-8") as f:
            json.dump(records, f, ensure_ascii=False, indent=2)

        print(f"Checkpoint saved ({model_name} - Email {email_no})")

    print(f"Final save → {outfile}\n")

# -------------------------
# EXECUTE
# -------------------------

if __name__ == "__main__":
    for model in MODELS:
        run_model(model)
