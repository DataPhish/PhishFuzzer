import pandas as pd
import json
import os
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
import seaborn as sns

# --- CONFIGURATION ---
FILES = {
    "Gemini-3.1-Pro": "../Results/results_raw_gemini.jsonl",
    "Qwen-2.5-72B": "../Results/results_raw_qwen.jsonl"
}
FIGURES_DIR = "figures"
LABELS = ["phishing", "spam", "valid"]

# ADJUST THIS TO CHANGE ALL TEXT SIZES AT ONCE
SCALE_FACTOR = 0.9 

def ensure_figures_dir():
    if not os.path.exists(FIGURES_DIR):
        os.makedirs(FIGURES_DIR)

def load_data(file_path):
    data = []
    if not os.path.exists(file_path): return None
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            try:
                row = json.loads(line)
                if row.get("run", 1) != 1: continue
                data.append(row)
            except Exception: continue
    return pd.DataFrame(data) if data else None

def generate_comparison(model_name, file_path):
    df = load_data(file_path)
    if df is None: return
    for col in ["prediction", "ground_truth", "prompt_type"]:
        df[col] = df[col].astype(str).str.lower().str.strip()

    fig = plt.figure(figsize=(8.5, 4.0))
    gs = fig.add_gridspec(1, 3, width_ratios=[1, 1, 0.05], wspace=0.15)
    ax1 = fig.add_subplot(gs[0]); ax2 = fig.add_subplot(gs[1], sharey=ax1); cbar_ax = fig.add_subplot(gs[2])

    for i, p_type in enumerate(["basic", "full"]):
        ax = [ax1, ax2][i]
        subset = df[df["prompt_type"] == p_type]
        cm = pd.crosstab(subset["ground_truth"], subset["prediction"]).reindex(index=LABELS, columns=LABELS, fill_value=0)

        sns.heatmap(cm, annot=True, fmt="d", cmap="Blues", ax=ax, cbar=(i==1), cbar_ax=cbar_ax if i==1 else None,
                    annot_kws={"size": 12 * SCALE_FACTOR, "weight": "bold"}, yticklabels=True)

        ax.set_aspect('equal', adjustable='box')
        ax.set_title(f"{model_name}: {p_type.upper()}", fontsize=11 * SCALE_FACTOR, weight='bold', pad=8)
        ax.set_xlabel("Predicted Label", fontsize=10 * SCALE_FACTOR)
        
        if i == 0:
            ax.set_ylabel("Actual Label", fontsize=11 * SCALE_FACTOR, fontweight='bold', labelpad=8)
            ax.set_yticklabels(LABELS, rotation=0, fontsize=9 * SCALE_FACTOR)
        else:
            ax.set_ylabel("")
            plt.setp(ax.get_yticklabels(), visible=False)
            ax.tick_params(left=False)
        ax.tick_params(axis="x", labelsize=9 * SCALE_FACTOR)

    plt.savefig(os.path.join(FIGURES_DIR, f"confusion_{model_name.lower().replace('.','').replace('-','_')}.pdf"), bbox_inches='tight')

if __name__ == "__main__":
    ensure_figures_dir()
    for name, path in FILES.items():
        generate_comparison(name, path)
    plt.show()