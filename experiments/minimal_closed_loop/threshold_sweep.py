from __future__ import annotations

import argparse
from dataclasses import replace
from pathlib import Path

import numpy as np
import pandas as pd

from simulator import SimConfig, fused_risk_map, lidar_health_map, load_sdf_box_world, run_simulation, visual_health_map


def main() -> None:
    parser = argparse.ArgumentParser(description="Sweep stabilization thresholds for the gated policy.")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(__file__).parent / "results_gated",
        help="Output directory (default: results_gated next to this script).",
    )
    parser.add_argument("--seeds", type=int, default=5, help="Number of deterministic seeds per cell.")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[2]
    sdf = root / "projects/autonomous-exploration-demo-benchmark/simulation/worlds/corridor/corridor.world"
    args.output_dir.mkdir(parents=True, exist_ok=True)
    out = args.output_dir / "threshold_sweep.csv"
    world = load_sdf_box_world(sdf)
    lidar = lidar_health_map(world)
    records = []
    for scenario in ("visual_degradation", "complementary", "common_mode"):
        visual = visual_health_map(world, scenario)
        scenario_lidar = lidar.copy()
        if scenario == "visual_degradation":
            scenario_lidar[world.occupancy == 0] = np.maximum(scenario_lidar[world.occupancy == 0], 0.78)
        health = (visual, scenario_lidar, fused_risk_map(world, visual, scenario_lidar, scenario))
        for threshold in (0.50, 0.75, 1.00, 1.25, 1.50):
            # Disable the new detour constraint here so this sweep isolates the
            # effect of the uncertainty trigger threshold.
            cfg = replace(SimConfig(), stabilization_threshold=threshold, recovery_detour_budget_m=float("inf"))
            for seed in range(args.seeds):
                result = run_simulation(world, "cross_modal_risk", seed, scenario, cfg, health)
                records.append({"scenario": scenario, "threshold": threshold, **result.as_dict()})
    df = pd.DataFrame(records)
    df.to_csv(out, index=False)
    summary = df.groupby(["scenario", "threshold"])[["path_m", "pose_rmse_m", "failure_steps", "stabilization_revisits"]].mean().round(4)
    (out.parent / "threshold_sweep.md").write_text(
        "# Stabilization-threshold sensitivity\n\n"
        f"{args.seeds} seeded synthetic trials per cell. This is a design sensitivity check, not a statistical paper result.\n\n"
        "```text\n" + summary.to_string() + "\n```\n",
        encoding="utf-8",
    )
    print(summary.to_string())


if __name__ == "__main__":
    main()
