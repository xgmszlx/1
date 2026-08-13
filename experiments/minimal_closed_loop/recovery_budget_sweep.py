from __future__ import annotations

import argparse
from dataclasses import replace
from pathlib import Path

import numpy as np
import pandas as pd

from simulator import SimConfig, fused_risk_map, lidar_health_map, load_sdf_box_world, run_simulation, visual_health_map


SCENARIOS = ("visual_degradation", "complementary", "common_mode")


def main() -> None:
    parser = argparse.ArgumentParser(description="Sweep the conservative recovery-detour budget.")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(__file__).parent / "results_budgeted",
    )
    parser.add_argument("--seeds", type=int, default=5)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    root = Path(__file__).resolve().parents[2]
    sdf = root / "projects/autonomous-exploration-demo-benchmark/simulation/worlds/corridor/corridor.world"
    world = load_sdf_box_world(sdf)
    lidar = lidar_health_map(world)
    records = []
    for scenario in SCENARIOS:
        visual = visual_health_map(world, scenario)
        scenario_lidar = lidar.copy()
        if scenario == "visual_degradation":
            scenario_lidar[world.occupancy == 0] = np.maximum(scenario_lidar[world.occupancy == 0], 0.78)
        health = (visual, scenario_lidar, fused_risk_map(world, visual, scenario_lidar, scenario))
        for budget_m in (0.0, 4.0, 8.0, 12.0, 16.0):
            cfg = replace(SimConfig(), recovery_detour_budget_m=budget_m)
            for seed in range(args.seeds):
                result = run_simulation(world, "cross_modal_risk", seed, scenario, cfg, health)
                records.append({"scenario": scenario, "budget_m": budget_m, **result.as_dict()})

    df = pd.DataFrame(records)
    csv_path = args.output_dir / "recovery_budget_sweep.csv"
    df.to_csv(csv_path, index=False)
    metrics = ["path_m", "pose_rmse_m", "failure_steps", "stabilization_revisits", "recovery_budget_spent_m"]
    summary = df.groupby(["scenario", "budget_m"])[metrics].mean().round(4)
    (args.output_dir / "recovery_budget_sweep.md").write_text(
        "# Recovery-detour-budget sensitivity\n\n"
        f"{args.seeds} seeded synthetic trials per cell. The budget is a conservative twice-anchor-distance estimate. "
        "This is a mechanism sensitivity test, not SLAM evidence.\n\n"
        "```text\n" + summary.to_string() + "\n```\n",
        encoding="utf-8",
    )
    print(summary.to_string())


if __name__ == "__main__":
    main()
