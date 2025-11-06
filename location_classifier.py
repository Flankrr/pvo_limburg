# This file trains a logistic regression classifier to identify whether a token is likely a Dutch location name.
# This is needed because the pre-trained NER(Named Entity Recognition) model we use sometimes returns words that
# not locations and these needs to be filtered out somehow.
# It now simply overwrites the existing .pkl model each time it runs.
# -------------------------------------------------------
import os
import pandas as pd
import joblib
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import classification_report

# -------------------------------------------------------
# Paths & output dirs
# -------------------------------------------------------
LATEST_PATH = "models/location_classifier_latest.pkl"
os.makedirs(os.path.dirname(LATEST_PATH), exist_ok=True)

# -------------------------------------------------------
# 1. Load the labeled dataset
# -------------------------------------------------------
df = pd.read_csv("location_candidates_for_labeling.csv")
df["label"] = df["label"].astype(int)

# -------------------------------------------------------
# 2. Load the GeoNames gazetteer (NL, BE, DE)
# -------------------------------------------------------
from geoNames.gazetteer_parser import load_geonames_file

nl_gaz = load_geonames_file("geoNames/NL.txt", keep_countries={"NL"})
be_gaz = load_geonames_file("geoNames/BE.txt", keep_countries={"BE"})
de_gaz = load_geonames_file("geoNames/DE.txt", keep_countries={"DE"})

gazetteer = {}
for g in (nl_gaz, be_gaz, de_gaz):
    gazetteer.update(g)

print(f"Gazetteer loaded with {len(gazetteer):,} place names")

# -------------------------------------------------------
# 3. Dutch location name patterns (suffixes & prefixes)
# -------------------------------------------------------

DUTCH_SUFFIXES = [
    # Water-related
    "dijk", "dam", "meer", "veen", "waard", "weerd",
    # Land & terrain
    "land", "veld", "velde", "bos", "bosch", "heide", "horst",
    # Elevation
    "berg", "heuvel", "loo",
    # Settlements
    "dorp", "kerk", "hoven", "huizen", "burg", "borg", "wijk", "stede", "stad",
    # Other
    "broek", "holt", "hout", "mond", "haven", "rijk", "gaarde", "staat",
]

DUTCH_PREFIXES = [
    "noord", "zuid", "oost", "west",
    "nieuw", "oud",
    "’s", "s-", "st-",
]

# -------------------------------------------------------
# 4. Feature extraction
# -------------------------------------------------------
def extract_features(word: str) -> dict:
    """Extract basic lexical and gazetteer-based features for each candidate."""
    w = str(word)
    wl = w.lower()
    return {
        "length": len(w),
        "num_digits": sum(ch.isdigit() for ch in w),
        "has_dash": int("-" in w),
        "has_space": int(" " in w),
        "starts_upper": int(bool(w) and w[0].isupper()),
        "all_upper": int(w.isupper()),
        "in_gazetteer": int(wl in gazetteer),
        "contains_gemeente": int("gemeente" in wl),
        "contains_stad": int("stad" in wl),
        "contains_provincie": int("provincie" in wl),

        # Dutch-specific morphology
        **{f"ends_with_{suf}": int(wl.endswith(suf)) for suf in DUTCH_SUFFIXES},
        **{f"starts_with_{pre}": int(wl.startswith(pre)) for pre in DUTCH_PREFIXES},
    }

# -------------------------------------------------------
# 5. Build feature matrix
# -------------------------------------------------------
features = pd.DataFrame([extract_features(w) for w in df["word"]])
y = df["label"]

# -------------------------------------------------------
# 6. Train/test split
# -------------------------------------------------------
X_train, X_test, y_train, y_test = train_test_split(
    features, y, test_size=0.2, random_state=42, stratify=y
)

# -------------------------------------------------------
# 7. Train logistic regression classifier
# -------------------------------------------------------
clf = LogisticRegression(max_iter=1000)
clf.fit(X_train, y_train)

# -------------------------------------------------------
# 8. Evaluate on test set
# -------------------------------------------------------
y_pred = clf.predict(X_test)
print("\n=== Classification Report ===")
print(classification_report(y_test, y_pred))

# -------------------------------------------------------
# 9. Save model (overwrite existing file)
# -------------------------------------------------------
model_blob = {"model": clf, "feature_columns": list(features.columns)}
joblib.dump(model_blob, LATEST_PATH)
print(f"\n✅ Model saved (overwritten) → {LATEST_PATH}")

# -------------------------------------------------------
# 10. Cross-validation (for robustness)
# -------------------------------------------------------
scores = cross_val_score(clf, features, y, cv=5, scoring="f1_macro")
print("Average F1:", scores.mean())
