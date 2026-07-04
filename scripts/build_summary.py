"""원본 CSV로 data/summary.json을 다시 만드는 간단한 보조 스크립트입니다.

사용법:
1. 원본 파일을 data/raw/cache_based_clean_dataset.csv 위치에 둡니다.
2. 프로젝트 루트에서 `python scripts/build_summary.py`를 실행합니다.
"""
from __future__ import annotations

import json
from pathlib import Path

import csv

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw" / "cache_based_clean_dataset.csv"
OUT = ROOT / "data" / "summary.json"


def safe_float(value: str) -> float | None:
    try:
        if value == "" or value.lower() == "nan":
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def main() -> None:
    if not RAW.exists():
        raise FileNotFoundError(f"원본 CSV를 찾을 수 없습니다: {RAW}")

    total_rows = 0
    date_start = None
    date_end = None
    o3_sum = 0.0
    o3_count = 0
    o3_min = float("inf")
    o3_max = float("-inf")
    hourly_sum = {str(h): 0.0 for h in range(24)}
    hourly_count = {str(h): 0 for h in range(24)}
    monthly_sum = {}
    monthly_count = {}
    yearly_sum = {}
    yearly_count = {}

    with RAW.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        columns = reader.fieldnames or []
        station_names = [c.replace("station_", "") for c in columns if c.startswith("station_")]

        for row in reader:
            total_rows += 1
            dt = row.get("datetime", "")[:10]
            if dt:
                date_start = dt if date_start is None else min(date_start, dt)
                date_end = dt if date_end is None else max(date_end, dt)

            o3 = safe_float(row.get("O3", ""))
            if o3 is None:
                continue

            o3_sum += o3
            o3_count += 1
            o3_min = min(o3_min, o3)
            o3_max = max(o3_max, o3)

            hour = row.get("hour", "")
            month = row.get("month", "")
            year = row.get("year", "")
            if hour in hourly_sum:
                hourly_sum[hour] += o3
                hourly_count[hour] += 1
            if month:
                monthly_sum[month] = monthly_sum.get(month, 0.0) + o3
                monthly_count[month] = monthly_count.get(month, 0) + 1
            if year:
                yearly_sum[year] = yearly_sum.get(year, 0.0) + o3
                yearly_count[year] = yearly_count.get(year, 0) + 1

    summary = {
        "dataset": {
            "rows": total_rows,
            "date_start": date_start,
            "date_end": date_end,
            "features_total": len(columns),
            "station_count": len(station_names),
            "station_names": station_names,
        },
        "metrics": {
            "mean_O3": o3_sum / o3_count,
            "min_O3": o3_min,
            "max_O3": o3_max,
        },
        "hourly_o3": {h: hourly_sum[h] / hourly_count[h] for h in hourly_sum if hourly_count[h]},
        "monthly_o3": {m: monthly_sum[m] / monthly_count[m] for m in monthly_sum if monthly_count[m]},
        "yearly_o3": {y: yearly_sum[y] / yearly_count[y] for y in yearly_sum if yearly_count[y]},
    }

    OUT.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"요약 파일 생성 완료: {OUT}")


if __name__ == "__main__":
    main()
