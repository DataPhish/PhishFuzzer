import pandas as pd
import json
import os
import matplotlib
matplotlib.use("Agg") 
import matplotlib.pyplot as plt
import numpy as np

# =====================================
# CONFIG & PATHS
# =====================================
FILES = {
    "Gemini-3.1-Pro": "../Results/results_raw_gemini.jsonl",
    "Qwen-2.5-72B": "../Results/results_raw_qwen.jsonl"
}
FIGURES_DIR = "figures"

# Palette: Dark for Seeds, Light for Variants
COLOR_MAP = {
    "priv_seed": "#C97C5D",   # muted terracotta
    "pub_seed":  "#4C72B0",   # muted steel blue
    "priv_var":  "#E6B8A2",   # soft peach
    "pub_var":   "#9FBCE6"    # soft sky blue
}

def ensure_figures_dir():
    if not os.path.exists(FIGURES_DIR):
        os.makedirs(FIGURES_DIR)

def load_and_prep(path):
    rows = []
    if not os.path.exists(path):
        print(f"File not found: {path}")
        return None
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            try: 
                rows.append(json.loads(line))
            except: 
                continue
    
    df = pd.DataFrame(rows)
    for col in ["prediction", "ground_truth", "source", "dataset", "prompt_type"]:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip().str.lower()
    
    df["is_correct"] = (df["prediction"] == df["ground_truth"]).astype(int)
    
    # Map provenance: 'manual' is Private, others are Public
    seed_provenance = df[df["dataset"] == "original"][["original_seed_id", "source"]].drop_duplicates()
    prov_map = dict(zip(seed_provenance["original_seed_id"], seed_provenance["source"]))
    df["inherited_source"] = df["original_seed_id"].map(prov_map)
    return df

def get_stats_by_model(df):
    results_by_prompt = {}
    core_df = df[df["original_seed_id"] <= 3300].copy()

    for p_type in ["basic", "full"]:
        subset = core_df[core_df["prompt_type"] == p_type].copy()
        if subset.empty:
            results_by_prompt[p_type] = None
            continue
            
        stats = {}
        for ds in ["original", "rephrased"]:
            ds_subset = subset[subset["dataset"] == ds]
            stats[ds] = {
                "private": {
                    "acc": ds_subset[ds_subset["inherited_source"] == "manual"]["is_correct"].mean(),
                    "n": len(ds_subset[ds_subset["inherited_source"] == "manual"])
                },
                "public": {
                    "acc": ds_subset[ds_subset["inherited_source"] != "manual"]["is_correct"].mean(),
                    "n": len(ds_subset[ds_subset["inherited_source"] != "manual"])
                }
            }
        results_by_prompt[p_type] = stats
    return results_by_prompt

def plot_provenance_comparison(results_by_prompt, model_label):
    fig, axes = plt.subplots(1, 2, figsize=(10, 5), sharey=True)
    prompt_types = ["basic", "full"]
    
    # Updated labels to your requested order
    x_labels = ["Private\nSeed", "Public\nSeed", "Private\nVariant", "Public\nVariant"]
    x_pos = np.arange(len(x_labels))

    for i, p_type in enumerate(prompt_types):
        stats = results_by_prompt[p_type]
        if stats is None: continue
            
        # Re-ordered data points for the new sequence
        data_points = [
            (stats["original"]["private"],  COLOR_MAP["priv_seed"]), # Private Seed
            (stats["original"]["public"],   COLOR_MAP["pub_seed"]),  # Public Seed
            (stats["rephrased"]["private"], COLOR_MAP["priv_var"]),  # Private Variant
            (stats["rephrased"]["public"],  COLOR_MAP["pub_var"])    # Public Variant
        ]
        
        for idx, (data, color) in enumerate(data_points):
            acc = data["acc"] if not np.isnan(data["acc"]) else 0
            axes[i].bar(idx, acc, width=0.7, color=color, edgecolor='black', linewidth=0.8)
            
            axes[i].text(idx, acc + 0.01, f"{acc:.2f}\n$n$={data['n']}", 
                         ha='center', va='bottom', fontsize=10, fontweight='bold')

        axes[i].set_title(f"{model_label}: {p_type.upper()}", fontsize=13, fontweight='bold', pad=15)
        axes[i].set_xticks(x_pos)
        axes[i].set_xticklabels(x_labels, fontsize=11)
        axes[i].set_ylabel("Accuracy Score" if i == 0 else "", fontsize=12)
        axes[i].set_ylim(0, 1.15) 
        axes[i].grid(axis='y', linestyle='--', alpha=0.3)

    plt.tight_layout()
    
    clean_name = model_label.lower().replace("-", "_").replace(".", "")
    save_path = os.path.join(FIGURES_DIR, f"provenance_{clean_name}.pdf")
    plt.savefig(save_path, bbox_inches='tight')
    print(f"Saved: {save_path}")
    plt.close()

if __name__ == "__main__":
    ensure_figures_dir()
    for name, path in FILES.items():
        df_model = load_and_prep(path)
        if df_model is not None:
            stats = get_stats_by_model(df_model)
            plot_provenance_comparison(stats, name)