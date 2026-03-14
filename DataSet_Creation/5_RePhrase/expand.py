#!/usr/bin/env python3

import os
import sys
import json
import time
import requests
import re
import logging

# ==========================
# CONFIG
# ==========================

INPUT_FILE = "emails_normalized.json"
OUTPUT_FILE = "emails_expanded_2026_Gemini.json"
LOG_FILE = "expansion.log"

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
API_KEY = os.getenv("OPENROUTER_API_KEY")

if not API_KEY:
    sys.exit("ERROR: Please export OPENROUTER_API_KEY")

MODEL_ID = "google/gemini-2.5-flash"

TEMPERATURE = 0.7
MAX_TOKENS = 6000
TIMEOUT = 180
SLEEP_SEC = 0.8
MAX_RETRIES = 2

# ==========================
# LOGGING
# ==========================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(sys.stdout)
    ]
)

logging.info("=== Synthetic Expansion Started ===")

# ==========================
# IMPORT PROMPTS
# ==========================

from prompts import (
    GLOBAL_RULES,
    PHISHING_WELL_PROMPT,
    PHISHING_FAKE_PROMPT,
    SPAM_WELL_PROMPT,
    SPAM_FAKE_PROMPT,
    VALID_WELL_PROMPT,
    VALID_FAKE_PROMPT
)

# ==========================
# HELPERS
# ==========================

def safe_json_array(raw: str):
    try:
        return json.loads(raw)
    except Exception:
        match = re.search(r"\[[\s\S]*\]", raw)
        if match:
            try:
                return json.loads(match.group(0))
            except Exception:
                return None
    return None


def call_openrouter(prompt: str) -> str:
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
    }

    r = requests.post(
        OPENROUTER_URL,
        headers=headers,
        json=payload,
        timeout=TIMEOUT
    )

    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"]


def build_prompt(template: str, email: dict) -> str:
    original_json = json.dumps(email, ensure_ascii=False, indent=2)
    full_prompt = GLOBAL_RULES + "\n\n" + template
    return full_prompt.replace("<INSERT ORIGINAL EMAIL JSON HERE>", original_json)


def normalize_variant_url_field(url_value):
    if url_value is None:
        return None
    if isinstance(url_value, list):
        cleaned = [u.strip() for u in url_value if isinstance(u, str) and u.strip()]
        return cleaned if cleaned else None
    if isinstance(url_value, str):
        val = url_value.strip()
        return [val] if val else None
    return None


def compute_safe_new_id(seed_dataset, expanded_dataset):
    max_id = 0

    for e in seed_dataset:
        n = e.get("No.")
        if isinstance(n, int) and n > max_id:
            max_id = n

    for e in expanded_dataset:
        n = e.get("No.")
        if isinstance(n, int) and n > max_id:
            max_id = n

    return max_id + 1


# ==========================
# LOAD DATA
# ==========================

if not os.path.exists(INPUT_FILE):
    logging.error("Input file not found")
    sys.exit("Input file not found")

with open(INPUT_FILE, "r", encoding="utf-8") as f:
    seed_dataset = json.load(f)

logging.info(f"Loaded {len(seed_dataset)} seed emails")

# Ensure seeds have Original_ID
for e in seed_dataset:
    if e.get("Original_ID") is None:
        e["Original_ID"] = e.get("No.")

# ==========================
# RESUME SUPPORT
# ==========================

if os.path.exists(OUTPUT_FILE):
    logging.info("Existing output detected. Resuming.")
    with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
        expanded_dataset = json.load(f)
else:
    expanded_dataset = []

new_id = compute_safe_new_id(seed_dataset, expanded_dataset)
logging.info(f"Starting new IDs from {new_id}")

# ==========================
# MAIN LOOP
# ==========================

for idx, email in enumerate(seed_dataset, 1):

    seed_no = email.get("No.")
    seed_original_id = email.get("Original_ID")

    logging.info(f"Processing Seed {idx}/{len(seed_dataset)} | No: {seed_no}")

    # Ensure original seed exists in output
    if not any(e.get("No.") == seed_no for e in expanded_dataset):
        expanded_dataset.append(email)

    existing_for_seed = [
        e for e in expanded_dataset
        if e.get("Original_ID") == seed_original_id
    ]

    well_count = sum(
        1 for e in existing_for_seed
        if e.get("Entity_Type") == "well_known"
    )

    fake_count = sum(
        1 for e in existing_for_seed
        if e.get("Entity_Type") == "fabricated"
    )

    well_done = well_count >= 3
    fake_done = fake_count >= 3

    if well_done and fake_done:
        logging.info(f"Seed {seed_no} already complete. Skipping.")
        continue

    email_type = email.get("Type")

    if email_type == "Phishing":
        prompt_set = [
            ("well_known", PHISHING_WELL_PROMPT),
            ("fabricated", PHISHING_FAKE_PROMPT)
        ]
    elif email_type == "Spam":
        prompt_set = [
            ("well_known", SPAM_WELL_PROMPT),
            ("fabricated", SPAM_FAKE_PROMPT)
        ]
    elif email_type == "Valid":
        prompt_set = [
            ("well_known", VALID_WELL_PROMPT),
            ("fabricated", VALID_FAKE_PROMPT)
        ]
    else:
        logging.warning(f"Unknown Type for seed {seed_no}")
        continue

    for entity_type, template in prompt_set:

        if entity_type == "well_known" and well_done:
            continue
        if entity_type == "fabricated" and fake_done:
            continue

        prompt = build_prompt(template, email)

        for attempt in range(MAX_RETRIES):
            try:
                raw = call_openrouter(prompt)
                variants = safe_json_array(raw)

                if not variants or len(variants) != 3:
                    raise ValueError("Invalid JSON returned")

                length_labels = ["short", "medium", "long"]

                for i, variant in enumerate(variants):
                    new_email = {
                        "No.": new_id,
                        "Original_ID": seed_original_id,
                        "Subject": variant.get("Subject"),
                        "Body": variant.get("Body"),
                        "Sender": variant.get("From"),
                        "URL": normalize_variant_url_field(variant.get("URL(s)")),
                        "File": variant.get("File"),
                        "Type": email.get("Type"),
                        "Motivation": email.get("Motivation"),
                        "Created by": "LLM",
                        "Source": "Synthetic Entity-Seed Expansion 2026",
                        "Year": 2026,
                        "Entity_Type": entity_type,
                        "Length_Type": length_labels[i],
                    }

                    expanded_dataset.append(new_email)
                    new_id += 1

                logging.info(f"✓ Generated 3 {entity_type} variants for seed {seed_no}")
                break

            except Exception as e:
                logging.warning(f"Retry {attempt+1} failed for seed {seed_no}: {e}")
                time.sleep(1)

        time.sleep(SLEEP_SEC)

    # Progressive save
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(expanded_dataset, f, ensure_ascii=False, indent=2)

logging.info("=== Expansion Complete ===")