#!/usr/bin/env python3
"""Add strictly backward-looking health statistics to an extracted health table."""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd


SIGNALS = [
    "visual_inlier_ratio",
    "features",
    "icp_inliers_ratio",
    "icp_structural_complexity",
    "icp_correspondences",
    "scan_valid_ratio",
    "cov_trace_xyyaw",
]


def add_causal_features(frame: pd.DataFrame, windows_s: tuple[float, ...]) -> pd.DataFrame:
    result = frame.sort_values("stamp").reset_index(drop=True).copy()
    time_index = pd.to_timedelta(result.stamp - float(result.stamp.iloc[0]), unit="s")

    # RTAB-Map uses a very large covariance as a lost-state sentinel.  Preserve
    # ordering but prevent that sentinel from dominating linear scaling.
    result["cov_log1p"] = np.log1p(np.clip(result.cov_trace_xyyaw, 0.0, 1_000.0))
    signals = [column if column != "cov_trace_xyyaw" else "cov_log1p" for column in SIGNALS]

    indexed = result.set_index(time_index)
    for window_s in windows_s:
        suffix = f"{window_s:g}s"
        for column in signals:
            series = indexed[column].astype(float)
            rolling = series.rolling(f"{window_s}s", min_periods=2)
            result[f"{column}__mean_{suffix}"] = rolling.mean().to_numpy()
            result[f"{column}__std_{suffix}"] = rolling.std(ddof=0).to_numpy()
            result[f"{column}__delta_{suffix}"] = (series - rolling.apply(lambda x: x[0], raw=True)).to_numpy()
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--windows-s", type=float, nargs="+", default=[1.0, 2.0])
    args = parser.parse_args()

    frame = pd.read_csv(args.input)
    result = add_causal_features(frame, tuple(args.windows_s))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(args.output, index=False)
    print(f"rows={len(result)} added_columns={len(result.columns) - len(frame.columns)}")


if __name__ == "__main__":
    main()
