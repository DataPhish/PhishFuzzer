import pandas as pd
import json
import os
import matplotlib.pyplot as plt
import seaborn as sns

# --- CONFIGURATION ---
FILES = {
    "Gemini-3.1-Pro": "../Results/results_raw_gemini.jsonl",
    "Qwen-2.5-72B": "../Results/results_raw_qwen.jsonl"
}

FIGURES_DIR = "figures"
CATEGORIES = ['phishing', 'spam', 'valid']

def ensure_figures_dir():
    if not os.path.exists(FIGURES_DIR):
        os.makedirs(FIGURES_DIR)

def load_processed_data(file_path):
    data = []
    if not os.path.exists(file_path): return None
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            try:
                row = json.loads(line)
                if row.get('original_seed_id', 9999) <= 3300:
                    data.append(row)
            except: continue
    
    df = pd.DataFrame(data)
    df['prediction'] = df['prediction'].astype(str).str.lower().str.strip()
    df['ground_truth'] = df['ground_truth'].astype(str).str.lower().str.strip()
    df['is_correct'] = (df['prediction'] == df['ground_truth']).astype(int)
    return df

def generate_side_by_side_tfs(all_dfs, prompt_type):
    # REDUCED SIZE: Changed figsize from (16, 7) to (12, 5) for a more compact look
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    
    for i, (model_name, df) in enumerate(all_dfs.items()):
        subset = df[df['prompt_type'] == prompt_type.lower()].copy()
        
        tsr_scores = subset.groupby('original_seed_id')['is_correct'].sum()
        tfs_ids = tsr_scores[tsr_scores == 0].index
        tfs_data = subset[subset['original_seed_id'].isin(tfs_ids)].copy()
        
        cm = pd.crosstab(
            tfs_data['ground_truth'], 
            tfs_data['prediction'], 
            normalize='index'
        ).reindex(index=CATEGORIES, columns=CATEGORIES, fill_value=0)

        # Borderless "Overall Matrix" style
        sns.heatmap(cm, 
                    annot=True, 
                    fmt='.2f', 
                    cmap='OrRd', 
                    ax=axes[i], 
                    annot_kws={"size": 11, "weight": "bold"}) # Slightly smaller font for smaller plot
        
        axes[i].set_title(f"{model_name}\nFailure (TSR=0) - {prompt_type.upper()}", 
                          fontsize=13, pad=10)
        axes[i].set_xlabel("Predicted Label", fontsize=10)
        axes[i].set_ylabel("Actual Label" if i == 0 else "", fontsize=10)
        
        display_labels = [c.capitalize() for c in CATEGORIES]
        axes[i].set_xticklabels(display_labels, fontsize=9)
        axes[i].set_yticklabels(display_labels, fontsize=9, rotation=0)

    plt.tight_layout()
    save_path = os.path.join(FIGURES_DIR, f'side_by_side_tfs_{prompt_type}.png')
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    print(f"Saved: {save_path}")
    plt.close()

if __name__ == "__main__":
    ensure_figures_dir()
    
    loaded_datasets = {}
    for name, path in FILES.items():
        print(f"Loading {name}...")
        df = load_processed_data(path)
        if df is not None:
            loaded_datasets[name] = df
            
    if loaded_datasets:
        for p_type in ["full", "basic"]:
            generate_side_by_side_tfs(loaded_datasets, p_type)