#!/usr/bin/env python3

import json
import os

# -------------------------
# CONFIG
# -------------------------

RESULTS_DIR = "."   # Change if needed

MODELS = [
    "claude",
    "gpt",
    "gemini",
    "qwen",
    "deepseek"
]

N_TRIES = 5

# -------------------------
# NORMALIZATION
# -------------------------

def normalize(label):
    if not label:
        return None
    return label.strip().lower()

# -------------------------
# LOAD MODEL RESULTS
# -------------------------

def load_results(model_name):
    path = os.path.join(RESULTS_DIR, f"{model_name}_results.json")

    if not os.path.exists(path):
        raise FileNotFoundError(f"{path} not found")

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

# -------------------------
# EVALUATION
# -------------------------

for model in MODELS:

    print("\n==============================")
    print(f"Evaluating: {model.upper()}")
    print("==============================")

    data = load_results(model)

    total = 0
    majority_correct = 0
    strict_correct = 0
    consistency_sum = 0

    wrong_ids = []
    unstable_ids = []

    for email in data:

        true_label = normalize(email.get("Motivation"))

        # Skip emails without ground truth
        if not true_label:
            continue

        total += 1

        predicted_majority = normalize(email.get(f"{model}_majority"))
        confidence = email.get(f"{model}_confidence", 0)
        consistency_sum += confidence

        # Collect individual tries
        tries = []
        for i in range(1, N_TRIES + 1):
            tries.append(normalize(email.get(f"{model}_try{i}")))

        # -------------------------
        # Majority Accuracy
        # -------------------------
        if predicted_majority == true_label:
            majority_correct += 1

        # -------------------------
        # Strict Accuracy (ALL tries correct)
        # -------------------------
        if all(t == true_label for t in tries):
            strict_correct += 1
        else:
            if predicted_majority != true_label:
                wrong_ids.append(email.get("No."))
            else:
                unstable_ids.append(email.get("No."))

    # -------------------------
    # METRICS
    # -------------------------

    majority_accuracy = majority_correct / total if total else 0
    strict_accuracy = strict_correct / total if total else 0
    avg_consistency = consistency_sum / total if total else 0

    print(f"Total evaluated emails: {total}")
    print(f"Majority Accuracy: {majority_accuracy:.4f}")
    print(f"Strict Accuracy (5/5 correct): {strict_accuracy:.4f}")
    print(f"Average Internal Consistency: {avg_consistency:.4f}")

    print("\nMajority-Correct but Unstable IDs:")
    print(f"Count: {len(unstable_ids)}")
    print(unstable_ids)

    print("\nFully Wrong IDs:")
    print(f"Count: {len(wrong_ids)}")
    print(wrong_ids)
