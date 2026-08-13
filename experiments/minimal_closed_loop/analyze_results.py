from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd


def paired_bootstrap(delta: np.ndarray, seed: int = 20260813, n: int = 20000) -> tuple[float, float]:
    rng = np.random.default_rng(seed)
    samples = rng.choice(delta, size=(n, len(delta)), replace=True).mean(axis=1)
    return tuple(float(v) for v in np.percentile(samples, [2.5, 97.5]))


def main() -> None:
    parser = argparse.ArgumentParser(description="Paired analysis for a minimum-experiment result directory.")
    parser.add_argument(
        "--results",
        type=Path,
        default=Path(__file__).parent / "results",
        help="Directory containing trials.csv (default: results next to this script).",
    )
    args = parser.parse_args()
    results = args.results.resolve()
    df = pd.read_csv(results / "trials.csv")
    rows = []
    for scenario in sorted(df.scenario.unique()):
        proposed = df[(df.scenario == scenario) & (df.policy == "cross_modal_risk")].sort_values("seed")
        for baseline in ("nearest", "information_gain", "distance_advantage", "visual_risk"):
            base = df[(df.scenario == scenario) & (df.policy == baseline)].sort_values("seed")
            for metric in ("path_m", "pose_rmse_m", "max_pose_error_m", "failure_steps"):
                delta = proposed[metric].to_numpy() - base[metric].to_numpy()
                lo, hi = paired_bootstrap(delta)
                rows.append(
                    {
                        "scenario": scenario,
                        "baseline": baseline,
                        "metric": metric,
                        "proposed_mean": proposed[metric].mean(),
                        "baseline_mean": base[metric].mean(),
                        "paired_delta": delta.mean(),
                        "bootstrap_95_low": lo,
                        "bootstrap_95_high": hi,
                    }
                )
    out = pd.DataFrame(rows)
    out.to_csv(results / "paired_effects.csv", index=False)
    focus = out[(out.baseline == "distance_advantage") & out.metric.isin(["path_m", "pose_rmse_m", "failure_steps"])]
    lines = [
        "# Paired effect summary",
        "",
        "Proposed minus distance-advantage baseline; 95% intervals are seeded paired bootstrap intervals over 10 trials. Synthetic proxy only.",
        "",
        "```text",
        focus.round(4).to_string(index=False),
        "```",
        "",
    ]
    (results / "paired_effects.md").write_text("\n".join(lines), encoding="utf-8")
    print(focus.round(4).to_string(index=False))


if __name__ == "__main__":
    main()
