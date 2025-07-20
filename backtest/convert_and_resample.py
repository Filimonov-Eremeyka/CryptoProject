from utils.data_utils import csv_to_parquet, resample

csv_to_parquet(r"data/history/SOLUSDT_1m.csv")
for tf in ("5m", "15m", "1h"):
    resample("SOLUSDT", tf)
