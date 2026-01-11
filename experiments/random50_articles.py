import json
import random

INPUT_FILE = "all_articles.json"
OUTPUT_FILE = "experiments/all_articles_geo_ex.json"

# === 1. Load original articles ===
with open(INPUT_FILE, "r", encoding="utf-8") as f:
    all_articles = json.load(f)

# Safety: ensure we have at least 250
if len(all_articles) < 250:
    raise ValueError(f"Dataset has only {len(all_articles)} articles, need 50.")

# === 2. Pick 2500 random articles ===
random.seed(42)  # reproducible
picked_250 = random.sample(all_articles, 275)

# === 3. Save to new JSON file ===
with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(picked_250, f, ensure_ascii=False, indent=2)

print(f"Saved 250 random articles → {OUTPUT_FILE}")
