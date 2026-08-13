from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


METRICS = [
    "visual_inlier_ratio",
    "features",
    "icp_inliers_ratio",
    "icp_structural_complexity",
    "icp_correspondences",
    "cov_trace_xyyaw",
    "scan_valid_ratio",
    "estimation_time_s",
]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    frame = pd.read_csv(args.input)
    if len(frame) < 10:
        raise ValueError("health CSV is too short for a smoke summary")
    missing = [column for column in METRICS if column not in frame]
    if missing:
        raise ValueError(f"missing health columns: {missing}")
    if frame.visual_inlier_ratio.nunique(dropna=True) <= 1:
        raise ValueError("visual health is constant")
    if frame.icp_inliers_ratio.nunique(dropna=True) <= 1:
        raise ValueError("ICP health is constant")
    if not (frame.icp_structural_complexity.fillna(0.0) > 0.0).any():
        raise ValueError("ICP structural complexity never becomes positive")

    stats = frame[METRICS].describe(percentiles=[0.05, 0.5, 0.95]).T
    lines = [
        "# OpenLORIS cafe1-1 health smoke summary",
        "",
        "This verifies that both visual and 2-D LiDAR/ICP online signals are emitted and non-constant. It is not a predictive-model result.",
        "",
        f"- Rows: {len(frame)}",
        f"- Duration represented: {frame.stamp.max() - frame.stamp.min():.3f} s",
        f"- Backend lost rows: {int(frame.lost.sum())}",
        "",
        "```text",
        stats.round(5).to_string(),
        "```",
        "",
    ]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(lines), encoding="utf-8")
    print(f"rows={len(frame)} duration_s={frame.stamp.max() - frame.stamp.min():.3f} lost={int(frame.lost.sum())}")


if __name__ == "__main__":
    main()
