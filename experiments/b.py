import json
import pandas as pd

INPUT_FILE = "experiments/all_articles_filtered_geo_ex.json"
OUTPUT_FILE = "experiments/geo_experiment_labeling.csv"

# 1. Load the 50 articles
with open(INPUT_FILE, "r", encoding="utf-8") as f:
    articles = json.load(f)

# Convert to DataFrame
df = pd.DataFrame(articles)

# 2. Ensure a consistent column for the found locations
# Change "found_location" below to your actual key used in the pipeline.
# Example keys you might have: "geo_location", "locations", "predicted_locations"
FOUND_LOCATION_KEY = "locations"   # ← change if needed

if FOUND_LOCATION_KEY not in df.columns:
    df[FOUND_LOCATION_KEY] = ""  # empty placeholder if not yet present

# 3. Create the empty real_location column
df["real_location"] = ""

# 4. Select only relevant columns for the CSV
out_df = df[["title", FOUND_LOCATION_KEY, "real_location"]]

# 5. Save CSV
out_df.to_csv(OUTPUT_FILE, index=False, encoding="utf-8")

print(f"Saved labeling CSV → {OUTPUT_FILE}")
