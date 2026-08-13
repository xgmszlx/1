# OpenLORIS localization-health gate

Purpose: test whether lightweight RTAB-Map and scan statistics predict
near-future localization error/failure on public, sensor-matched data before any
ROS2 planner implementation.

This experiment uses the already-installed ROS Noetic RTAB-Map 0.21.13 only as
an offline prototype. The health interface is based on `rtabmap_msgs/OdomInfo`,
which is also present in the audited ROS2 branch.

## Stage A — acquisition and integrity

See `../../data/openloris/ACQUISITION.md`. Do not run on an incomplete bag.

## Stage B — backend replay

After inspecting the exact bag topics, launch RTAB-Map RGB-D odometry with scan
input and write the following runtime streams:

- `/rtabmap/odom_info`: visual and ICP health features;
- `/rtabmap/odom`: estimated pose;
- the input LaserScan: valid-return and range-distribution features.

`extract_health_csv.py` is a package-independent ROS1 node for those streams.
It never reads ground truth online.

OpenLORIS stores only one `CameraInfo` message in this bag. RTAB-Map's four-way
RGB/depth/info/scan message filter consumes calibration as part of each tuple,
so `repeat_camera_info.py` republishes the unchanged intrinsics with each RGB
timestamp. Without this adapter the backend produces no odometry; this is an
interface issue, not a tracking failure.

With `roscore` running, the complete cafe smoke command is:

```bash
bash active_slam_research/experiments/openloris_health/run_cafe1_pipeline.sh
```

The script uses `rgbdicp_odometry`, point-to-plane ICP, 20-neighbor scan
normals, no scan voxel filtering, and 0.25x bag speed. These parameters are
recorded for reproducibility and are not claimed to be optimized.

## Stage C — labels and split

Join the CSV to the official `gt_cafe_1.txt` timestamps offline. Align estimated
and ground-truth trajectories using one transform computed only from the
allowed initialization segment. Define labels over a fixed future horizon:

- translation-error growth;
- rotation-error growth;
- a *new* RTAB-Map `lost` state within the horizon, excluding frames already lost;
- thresholded failure event.

Do not use future absolute ATE alone as the primary label: cumulative drift
makes it mostly identify late trajectory time. The current smoke definition is
at least 0.05 m additional aligned position error over 1 s, plus a separately
reported new-lost event. The threshold must be frozen before testing another
scene.

One sequence is a pipeline smoke test only. A scientific test must calibrate on
one scene or run and evaluate on a different scene/run.

## Pre-registered model ladder

1. backend `lost` only;
2. covariance trace only;
3. visual-only logistic model;
4. LiDAR-only logistic model;
5. uncalibrated concatenated features;
6. calibrated cross-modal model (logistic plus isotonic or Platt calibration,
   fitted without access to the test scene).

Report AUROC and AUPRC, but make Brier score, expected calibration error, false
alarms per minute, and recall at a fixed false-alarm budget primary. Reject the
method route if the calibrated model does not improve over backend status and
covariance on held-out scenes.

Label the completed CSV with:

```bash
python active_slam_research/experiments/openloris_health/label_health_csv.py \
  --health-csv active_slam_research/experiments/openloris_health/results/cafe1-1-health.csv \
  --ground-truth active_slam_research/projects/openloris-scene-tools/benchmark/data/gt_cafe_1.txt \
  --sequence 1 \
  --output active_slam_research/experiments/openloris_health/results/cafe1-1-labeled.csv
```
