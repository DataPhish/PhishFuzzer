import json
import os
import requests
import time
import random
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock

# ======================================================
# CONFIG
# ======================================================

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

MODEL_NAME = "google/gemini-3.1-pro-preview"

N_RUNS = 1
MAX_WORKERS = 3   # parallel threads (safe)

RESULTS_DIR = "Results"
OUTPUT_FILE = os.path.join(RESULTS_DIR, "results_raw_gemini.jsonl")

HEADERS = {
    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
    "Content-Type": "application/json",
}

os.makedirs(RESULTS_DIR, exist_ok=True)
write_lock = Lock()

# ======================================================
# LOAD DATA
# ======================================================

def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

emails_original = load_json("../machinewars_emails_original_seed_v1.json")
emails_rephrased = load_json("../machinewars_emails_entity_rephrased_v1.json")

# ======================================================
# RESUME SUPPORT
# ======================================================

def load_completed():
    completed = set()
    if not os.path.exists(OUTPUT_FILE):
        return completed

    with open(OUTPUT_FILE, "r") as f:
        for line in f:
            row = json.loads(line)
            key = (
                row["dataset"],
                row["email_id"],
                row["model"],
                row["prompt_type"],
                row["run"]
            )
            completed.add(key)

    return completed

completed_set = load_completed()

# ======================================================
# PHASE COMPLETION CHECK
# ======================================================

def phase_completed(dataset_name, prompt_type, dataset_size):
    expected = dataset_size * N_RUNS
    count = 0

    if not os.path.exists(OUTPUT_FILE):
        return False

    with open(OUTPUT_FILE, "r") as f:
        for line in f:
            row = json.loads(line)
            if row["dataset"] == dataset_name and row["prompt_type"] == prompt_type:
                count += 1

    return count >= expected

# ======================================================
# PROMPTS
# ======================================================

SYSTEM_PROMPT = """You are a cybersecurity email classifier.

Classify the email into ONE of these categories:
- phishing
- spam
- valid

Respond with ONLY ONE WORD.
Do not explain.
"""

def build_basic_prompt(email):
    return f"""
Subject:
{email.get("Subject","")}

Body:
{email.get("Body","")}
"""

def build_full_prompt(email):
    return f"""
Subject:
{email.get("Subject","")}

Body:
{email.get("Body","")}

Sender:
{email.get("Sender","")}

URLs:
{email.get("URL","")}

Attachment:
{email.get("File","")}
"""

# ======================================================
# LLM QUERY WITH RETRIES
# ======================================================

def query_llm_single(prompt):

    max_retries = 6
    base_backoff = 5

    for attempt in range(max_retries):
        try:
            payload = {
                "model": MODEL_NAME,
                "temperature": 0.7,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt}
                ],
            }

            response = requests.post(
                OPENROUTER_URL,
                headers=HEADERS,
                json=payload,
                timeout=60
            )

            if response.status_code == 429:
                raise requests.exceptions.HTTPError("429")

            response.raise_for_status()
            result = response.json()

            text = result["choices"][0]["message"]["content"].strip().lower()

            if "phishing" in text:
                return "phishing"
            elif "spam" in text:
                return "spam"
            elif "valid" in text:
                return "valid"
            else:
                return "unknown"

        except requests.exceptions.HTTPError as e:
            if "429" in str(e):
                wait_time = base_backoff * (2 ** attempt) + random.uniform(0, 1)
                print(f"⚠ Rate limited. Waiting {wait_time:.1f} seconds...")
                time.sleep(wait_time)
                continue
            else:
                raise

    raise Exception("Max retries exceeded.")

# ======================================================
# PROCESS SINGLE EMAIL RUN
# ======================================================

def process_task(dataset_name, email, prompt_type, run):

    email_id = email["No."]
    original_seed_id = email.get("Original_ID")

    key = (dataset_name, email_id, MODEL_NAME, prompt_type, run)

    if key in completed_set:
        return None

    prompt = build_basic_prompt(email) if prompt_type == "basic" else build_full_prompt(email)
    prediction = query_llm_single(prompt)

    row = {
        "dataset": dataset_name,
        "email_id": email_id,
        "original_seed_id": original_seed_id,
        "model": MODEL_NAME,
        "prompt_type": prompt_type,
        "run": run,
        "prediction": prediction,
        "ground_truth": email.get("Type"),
        "source": email.get("Source"),
        "created_by": email.get("Created by"),
        "motivation": email.get("Motivation"),
        "year": email.get("Year"),
    }

    return row

# ======================================================
# PHASE ORDER
# ======================================================

PHASES = [
    ("original", "full"),
    ("original", "basic"),
    ("rephrased", "full"),
    ("rephrased", "basic"),
]

# ======================================================
# MAIN EXECUTION
# ======================================================

for dataset_name, prompt_type in PHASES:

    dataset = emails_original if dataset_name == "original" else emails_rephrased
    dataset_size = len(dataset)

    if phase_completed(dataset_name, prompt_type, dataset_size):
        print(f"Skipping completed phase: {dataset_name} | {prompt_type}")
        continue

    print(f"\n=== Running: {dataset_name} | {prompt_type} ===")

    tasks = []

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:

        for email in dataset:
            for run in range(1, N_RUNS + 1):
                tasks.append(
                    executor.submit(
                        process_task,
                        dataset_name,
                        email,
                        prompt_type,
                        run
                    )
                )

        for future in tqdm(as_completed(tasks),
                           total=len(tasks),
                           desc=f"{dataset_name} | {prompt_type}"):

            try:
                result = future.result()

                if result:
                    with write_lock:
                        with open(OUTPUT_FILE, "a", encoding="utf-8") as f:
                            f.write(json.dumps(result) + "\n")

                        completed_set.add((
                            result["dataset"],
                            result["email_id"],
                            result["model"],
                            result["prompt_type"],
                            result["run"]
                        ))

                        time.sleep(0.3)

            except Exception as e:
                print("Error:", e)

print("\nAll phases complete.")