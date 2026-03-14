import pandas as pd
import json
import os

# --- CONFIGURATION ---
FILES = {
    "Qwen-2.5-72B": "../Results/results_raw_qwen.jsonl",
    "Gemini-3.1-Pro": "../Results/results_raw_gemini.jsonl"
}

def load_and_filter(file_path):
    data = []
    if not os.path.exists(file_path):
        return None
    
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            try:
                row = json.loads(line)
                # Strict filter for the first 3300 original email families
                if row.get('original_seed_id', 9999) <= 3300:
                    data.append(row)
            except:
                continue
    df = pd.DataFrame(data)
    df['prediction'] = df['prediction'].str.lower().str.strip()
    df['ground_truth'] = df['ground_truth'].str.lower().str.strip()
    df['is_correct'] = (df['prediction'] == df['ground_truth']).astype(int)
    return df

def run_reliability_analysis():
    results = []
    
    for label, path in FILES.items():
        df = load_and_prep(path) if 'load_and_prep' in globals() else load_and_filter(path)
        
        for p_type in ['full', 'basic']:
            subset = df[df['prompt_type'] == p_type.lower()]
            if subset.empty: continue
            
            # Group by Seed ID to get Task Success Rate (TSR) per template
            # Each group size should be 7 (1 seed + 6 variants)
            template_scores = subset.groupby('original_seed_id')['is_correct'].sum()
            total_n = len(template_scores)
            
            # 1. Conf@7 (Model was bulletproof / 100% correct)
            conf_7_count = (template_scores == 7).sum()
            conf_7_pct = (conf_7_count / total_n) * 100
            
            # 2. TFS@7 (Model was blind / 0% correct across all versions)
            tfs_7_count = (template_scores == 0).sum()
            tfs_7_pct = (tfs_7_count / total_n) * 100
            
            results.append({
                "Model": label,
                "Prompt": p_type.upper(),
                "Families": total_n,
                "Conf@7 (n)": conf_7_count,
                "Conf@7 (%)": f"{conf_7_pct:.2f}%",
                "TFS@7 (n)": tfs_7_count,
                "TFS@7 (%)": f"{tfs_7_pct:.2f}%"
            })

    # Display results
    print("\n" + "="*85)
    print(f"{'RELIABILITY METRICS (N=3300 families)':^85}")
    print("="*85)
    final_df = pd.DataFrame(results)
    print(final_df.to_string(index=False))
    print("="*85)

if __name__ == "__main__":
    run_reliability_analysis()