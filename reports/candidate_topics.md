# Candidate topics and convergence decision

Status: stage-1 shortlist, 2026-08-13. Scores are comparative judgments grounded in the accompanying evidence matrix; they are not claims of novelty.

## Evaluation dimensions

Each item is scored from 1 (poor) to 5 (strong):

- **Gap**: how clearly the exact problem remains open after the verified literature search.
- **Build**: feasibility for a weak-code graduate student using modular open source; higher is easier.
- **Data**: suitability of public real data and interactive simulation.
- **Hardware**: match to RGB-D + 2-D LiDAR + IMU on a four-wheel indoor robot.
- **Paper**: ability to support a complete Q2/Q3-level story with rigorous baselines and ablations.
- **Risk**: resistance to obvious reviewer objections; higher is safer.

| Rank | Candidate | Gap | Build | Data | Hardware | Paper | Risk | Total / 30 |
|---:|---|---:|---:|---:|---:|---:|---:|---:|
| 1A | Calibrated cross-modal SLAM-health-aware exploration and recovery | 3 | 3 | 5 | 5 | 4 | 3 | **23** |
| 1B | Controlled-degradation benchmark plus a failure-aware ROS2 baseline | 4 | 4 | 4 | 5 | 3 | 3 | **23** |
| 3 | Probabilistic loop-closure success plus distance-advantage exploration | 3 | 3 | 4 | 4 | 4 | 3 | **21** |
| 4 | Uncertainty-frontier stopping plus efficient frontier ordering | 2 | 4 | 3 | 5 | 3 | 2 | **19** |
| 5 | ROS2 port/extension of prior-graph SLAM-aware exploration | 2 | 2 | 3 | 4 | 3 | 2 | **16** |

## Candidate 1A — higher-upside working direction

### Working title

**Calibrated Selective Recovery for Active RGB-D–2D-LiDAR SLAM under Complementary Degradation**

The title should remain provisional until the exact-match search and real-data health prediction results pass.

### Real problem

Indoor service robots encounter textureless/poorly illuminated transitions and geometrically repetitive corridors. A camera and 2-D LiDAR do not fail in exactly the same places. Existing active-planning papers largely score visual or LiDAR localizability separately; existing multi-sensor SLAM papers mainly improve state estimation but do not decide when exploration should continue, detour, slow down, or deliberately revisit a stable place.

ARAS already covers ambiguity-aware robust exploration/recovery, and LOCUS plus
CompSLAM already cover health-aware or complementary multi-modal estimation.
Consequently the gap score is reduced from 4 to 3: the publishable distinction
must be the calibrated low-cost RGB-D/2-D-LiDAR decision interface and bounded
false-recovery cost, not the words “robust,” “health-aware,” or “multi-modal.”

### Narrow research question

Can an online, lightweight and **cross-scenario calibrated** health score derived from RGB-D tracking, 2-D scan matching, and pose-graph state reduce localization failure and map error during active exploration, while an explicit recovery budget prevents material increases in completion distance and time?

### Testable hypotheses

- H1: modality-specific health features predict near-future localization error/failure on unseen OpenLORIS scenes better than either backend covariance or a single-modality feature count.
- H2: calibrated cross-modal fusion avoids false recovery actions when one modality degrades but the other still preserves localization.
- H3: event-triggered risk-aware frontier/path selection reduces ATE, maximum drift, map inconsistency, and tracking-loss events in closed loop with no more than a pre-registered path/time overhead.
- H4: the benefit remains after controlling for exploration ordering by comparing against nearest frontier, information gain, and distance advantage.

### Module stitching plan

1. **Stable licensed base**: ROS2 Nav2 + SLAM Toolbox benchmark initially; RTAB-Map ROS2 for RGB-D/scan/IMU integration.
2. **Visual health**: tracked feature count, inlier ratio, spatial dispersion, image gradient/blur, valid-depth fraction, and odometry residual/statistics exposed by the backend.
3. **2-D LiDAR health**: condition/eigenvalue ratios of a point-to-line scan-matching Hessian, valid-return ratio, and scan-match residual.
4. **Graph health/recovery value**: pose-graph connectivity or covariance proxy plus loop-closure opportunity, drawing on Placed/Castellanos and probabilistic active-loop-closure work.
5. **Exploration ordering**: distance advantage or the licensed ROS2 frontier core, rather than a generic gain-weighted sum.
6. **Decision layer**: calibrated risk with hysteresis and event triggers; normal exploration, risk-avoiding path/frontier choice, and stable-anchor revisit are explicit modes. A cumulative detour/recovery budget and benefit-per-extra-metre test bound recovery cost.

### Minimum publishable novelty

The novelty cannot be “we add camera and LiDAR scores.” It must include all three:

1. a calibrated cross-modal health model whose output has the same interpretation across scenes;
2. a decision rule that distinguishes single-modality degradation from common-mode failure and has an explicit unnecessary-recovery penalty;
3. a public, repeatable evaluation that connects offline failure prediction to closed-loop SLAM/map outcomes.

### Evaluation ladder

1. **Offline module** — OpenLORIS-Scene: predict error growth/tracking failure over a short horizon; report AUROC/AUPRC, Brier score or expected calibration error, false alarms per minute, and cross-scene generalization. Do not use future ground truth as an online input.
2. **Closed-loop simulation** — public ROS2 Corridor, Bookstore, and Warehouse worlds: inject controlled visual degradation, laser FoV/dropout/noise, wheel slip, and combinations. Report coverage, distance, time, ATE/RPE, map IoU/occupied-cell consistency, failures, recovery count, and CPU.
3. **Small real demonstration** — only after the public-data and simulator hypotheses pass. Use the user's robot to demonstrate integration, not as the sole quantitative evidence.
4. Use at least 10–20 seeded trials per simulated condition, confidence intervals/effect sizes, and pre-declared failure thresholds.

### Required baselines and ablations

- nearest frontier;
- information-gain frontier;
- distance advantage;
- visual-only localizability;
- LiDAR-only localizability;
- naive uncalibrated weighted fusion;
- cross-modal calibrated fusion without recovery;
- full method without graph/loop component;
- full method with fixed versus adaptive trigger.

### Fatal risks / go-no-go gates

- **No-go A**: health features cannot predict near-future errors across OpenLORIS scenes better than simple backend status/covariance.
- **No-go B**: the full planner needs more than roughly 10–20% extra path/time for a small or statistically unstable accuracy benefit.
- **No-go C**: RTAB-Map/SLAM Toolbox do not expose sufficiently reliable online residuals without invasive backend modification.
- **No-go D**: an exact-match peer-reviewed method is found that already performs calibrated RGB-D + 2-D LiDAR health-driven exploration/recovery on a ground robot.

## Candidate 1B — equal-score, lower-method-risk fallback

### Working title

**A Reproducible ROS2 Benchmark for Active SLAM under Complementary Visual–LiDAR Degradation**

### Contribution

Extend the licensed ROS2 exploration benchmark with synchronized degradation injection, SLAM accuracy/map metrics, seeded protocols, and a simple event-triggered recovery baseline. Link real-data corruption ranges to OpenLORIS measurements where possible.

### Why it is feasible

- The base already provides ROS2 Jazzy, Gazebo Harmonic, Nav2, SLAM Toolbox, three worlds, Docker, several frontier implementations, and efficiency metrics.
- The contribution is systems/evaluation work rather than a new SLAM backend.
- It directly addresses the T-RO survey's reproducibility gap.

### Main review risk

A benchmark without a new dataset or strong methodological insight may be judged as engineering. It needs validated degradation models, SLAM/map-quality metrics, multiple backends, and evidence that current planners change rank under realistic degradation.

## Candidate 3 — loop-oriented alternative

### Working title

**Failure-Probability-Calibrated Active Loop Closure for Efficient Indoor Exploration**

Combine distance advantage for normal exploration with the probabilistic active-loop-closure utility: probability of successful recognition times expected graph improvement minus travel cost. Calibrate recognition probability from OpenLORIS cross-session RGB-D/laser observations.

Advantages: clean mathematical story, explicit accuracy–distance trade-off, and direct relation to active SLAM rather than pure coverage.

Risks: ICRA 2024 already establishes the central utility; no official implementation was found; building reliable candidate loop correspondences and counterfactual graph updates may exceed the desired difficulty.

## Candidate 4 — uncertainty/stopping alternative

### Working title

**Uncertainty-Frontier Completion with Backtracking-Aware Ordering for Active SLAM**

Reimplement the UncertaintyMap/SiREn equations in a licensed ROS2 node, use distance advantage for ordering, and stop only when both coverage and calibrated spatial uncertainty meet requirements.

Advantages: intuitive, training-free, easy to explain, and sensor-agnostic.

Risks: RAS 2025 already contributes uncertainty frontiers, SiREn, and stopping; combining it with a better order may look incremental. Its official repository is unlicensed and under construction, so equations must be cleanly reimplemented.

## Candidate 5 — down-ranked

Port the RA-L 2024 prior topo-metric graph method to ROS2 and add online prior correction. This is technically meaningful, but prior maps are not part of the user's stated setup, pyconcorde/global routing adds burden, and the source paper already lists online prior-graph construction as future work. A port plus an expected extension is unlikely to be enough without a stronger new problem.

## Current decision

Proceed with Candidate 1, while packaging Candidate 2's reproducibility protocol as the evaluation contribution. Do **not** commit to a paper title yet. The next irreversible decision occurs only after:

1. exact-match literature search is exhausted enough to defend the gap;
2. minimum synthetic results show a reasonable risk/distance Pareto trade-off;
3. a small OpenLORIS subset can be acquired within disk constraints; and
4. RTAB-Map ROS2 health signals are verified in source/documentation.

## Minimum falsification result (2026-08-13)

The lightweight corridor experiment is a mechanism test using synthetic
localization error, not evidence of SLAM performance. After replacing an invalid
per-scenario risk normalization with one fixed calibration and requiring high
current fused risk before recovery:

- visual-only degradation caused **zero** unnecessary recovery actions and the
  cross-modal policy reduced to the distance-advantage behavior;
- complementary degradation reduced the synthetic pose-RMSE proxy from 0.4229 m
  to 0.2887 m, with paired 95% bootstrap interval for the change
  `[-0.1866, -0.0802]` m; failure events fell from 2.4 to 0.7 and path length
  changed from 56.50 m to 55.25 m;
- common-mode degradation reduced pose RMSE from 0.4886 m to 0.3573 m, but path
  length rose to 70.25 m (**+24.3%**), violating the pre-declared 10–20% gate;
  the failure-event interval also slightly crossed zero.

Therefore Candidate 1 survives only conditionally. The next mechanism version
must impose an explicit recovery-distance budget. If the accuracy gain then
disappears, Candidate 2 (benchmark plus failure-aware baseline) becomes the
more honest paper direction.

### Budgeted follow-up

A conservative cumulative detour budget was then added, charging twice the
shortest distance to a stable anchor. A five-seed sweep showed a discrete event:
budgets up to 12 m allowed no recovery, while 16 m allowed one recovery. The
16 m setting was then frozen for a 10-seed rerun. In common-mode degradation it
reduced the path from the unbudgeted 70.25 m to 61.50 m: **+8.85%** versus the
56.50 m distance-advantage baseline, inside the go/no-go gate. Pose-RMSE changed
from 0.4886 m to 0.3791 m (paired 95% interval `[-0.1781, -0.0420]` m), and
failure events changed from 3.3 to 1.9 (interval `[-2.6, -0.2]`).

This rescues the mechanism from immediate rejection, but the 16 m value is now
fixed for subsequent maps; it must not be retuned per map. The discrete one-
anchor behavior and synthetic error process remain major limitations.
