"""Exécute nettoyage + features et écrit data/processed/*.

Usage : python scripts/run_cleaning.py
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from voltride.cleaning import clean, load_raw  # noqa: E402
from voltride.features import add_features  # noqa: E402

raw = load_raw(ROOT / "data/raw/voltride_dataset_senior.csv")
df_clean, log = clean(raw)
df_clean = add_features(df_clean)

out = ROOT / "data/processed"
out.mkdir(parents=True, exist_ok=True)
df_clean.to_csv(out / "df_clean.csv", index=False, encoding="utf-8-sig")
log.to_csv(out / "journal_nettoyage.csv", index=False, encoding="utf-8-sig")
print(log.to_string(index=False))
print(f"\nraw={len(raw)}  clean={len(df_clean)}")
