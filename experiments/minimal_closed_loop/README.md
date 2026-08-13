# Minimum closed-loop falsification experiment

This experiment is deliberately smaller than a ROS/Gazebo reproduction. It tests whether the proposed decision logic is internally plausible before spending disk and setup time on a full stack.

It uses the Apache-2.0 `corridor.world` geometry from the public ROS2 autonomous-exploration benchmark. A 360-degree range sensor reveals an initially unknown occupancy grid. The simulator compares:

- nearest frontier;
- information-gain frontier selection;
- distance advantage (Ericson and Jensfelt, ECMR 2025, Eq. 5);
- visual-risk-aware distance advantage;
- cross-modal-risk-aware distance advantage with event-triggered stabilization revisits.

The current proposed policy additionally enforces a conservative cumulative
recovery-detour budget. The planned cost of a revisit is estimated as twice the
current shortest-path distance to its stable anchor, accounting for both the
backtrack and the need to regain exploration progress.

The localization model is a **synthetic proxy**, not a SLAM backend. Visual health is reduced in configured low-texture regions. 2-D LiDAR health is computed from the condition of a local point-to-line scan-matching information matrix. Independent modality variances are fused in information form. Pose error then follows a seeded random walk whose process variance is determined by fused health.

This experiment may reject a planner that has a poor risk/distance trade-off. It cannot establish a paper claim, because the corruption and pose-error model are simulated. Any surviving method must next be tested with OpenLORIS-Scene and a ROS2 closed-loop simulator.

Run:

```bash
python active_slam_research/experiments/minimal_closed_loop/run_experiment.py \
  --seeds 0:20 \
  --recovery-budget-m 16 \
  --output active_slam_research/experiments/minimal_closed_loop/results
```

Tests:

```bash
pytest -q active_slam_research/experiments/minimal_closed_loop/test_simulator.py
```

Sensitivity checks:

```bash
python active_slam_research/experiments/minimal_closed_loop/threshold_sweep.py
python active_slam_research/experiments/minimal_closed_loop/recovery_budget_sweep.py
```
