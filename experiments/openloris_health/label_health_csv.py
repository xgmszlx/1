#!/usr/bin/env python3
"""Join online health features to OpenLORIS ground truth and future labels."""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd


def wrap_angle(angle: np.ndarray) -> np.ndarray:
    return (angle + np.pi) % (2.0 * np.pi) - np.pi


def rotate_global_delta_to_local(delta_xy: np.ndarray, yaw: np.ndarray) -> np.ndarray:
    cosine = np.cos(yaw)
    sine = np.sin(yaw)
    return np.column_stack(
        (
            cosine * delta_xy[:, 0] + sine * delta_xy[:, 1],
            -sine * delta_xy[:, 0] + cosine * delta_xy[:, 1],
        )
    )


def read_openloris_ground_truth(path: Path, sequence: int) -> np.ndarray:
    rows: list[list[float]] = []
    active_sequence: int | None = None
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if line.startswith("seq:"):
            active_sequence = int(line.split(":", 1)[1])
            continue
        if not line or line.startswith(("scene:", "frame:")) or active_sequence != sequence:
            continue
        parts = line.split()
        if len(parts) != 8:
            continue
        rows.append([float(value) for value in parts])
    if not rows:
        raise ValueError(f"no ground-truth rows for sequence {sequence} in {path}")
    return np.asarray(rows, dtype=np.float64)


def quaternion_z_w_to_yaw(z: np.ndarray, w: np.ndarray) -> np.ndarray:
    return np.arctan2(2.0 * w * z, 1.0 - 2.0 * z * z)


def rigid_alignment_2d(source: np.ndarray, target: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Return R,t minimizing ||R source + t - target|| without scale."""
    source_mean = source.mean(axis=0)
    target_mean = target.mean(axis=0)
    covariance = (source - source_mean).T @ (target - target_mean)
    u, _, vt = np.linalg.svd(covariance)
    rotation = vt.T @ u.T
    if np.linalg.det(rotation) < 0.0:
        vt[-1, :] *= -1.0
        rotation = vt.T @ u.T
    translation = target_mean - rotation @ source_mean
    return rotation, translation


def label_dataframe(
    health: pd.DataFrame,
    ground_truth: np.ndarray,
    horizon_s: float,
    alignment_s: float,
    failure_position_m: float,
    growth_threshold_m: float = 0.05,
    rpe_threshold_m: float = 0.05,
) -> pd.DataFrame:
    result = health.copy().sort_values("stamp").reset_index(drop=True)
    stamps = result.stamp.to_numpy(dtype=np.float64)
    gt_t = ground_truth[:, 0]
    in_range = (stamps >= gt_t[0]) & (stamps <= gt_t[-1])
    result = result.loc[in_range].reset_index(drop=True)
    if len(result) < 10:
        raise ValueError("fewer than 10 health rows overlap ground truth")
    stamps = result.stamp.to_numpy(dtype=np.float64)

    gt_x = np.interp(stamps, gt_t, ground_truth[:, 1])
    gt_y = np.interp(stamps, gt_t, ground_truth[:, 2])
    gt_yaw_raw = quaternion_z_w_to_yaw(ground_truth[:, 6], ground_truth[:, 7])
    gt_yaw = np.interp(stamps, gt_t, np.unwrap(gt_yaw_raw))

    odom_xy = result[["odom_x_m", "odom_y_m"]].to_numpy(dtype=np.float64)
    valid = np.all(np.isfinite(odom_xy), axis=1) & np.isfinite(result.odom_yaw_rad.to_numpy())
    align = valid & (stamps <= stamps[valid][0] + alignment_s)
    if np.count_nonzero(align) < 5:
        align = valid & (np.arange(len(result)) < 50)
    if np.count_nonzero(align) < 5:
        raise ValueError("insufficient valid odometry for rigid alignment")

    rotation, translation = rigid_alignment_2d(odom_xy[align], np.column_stack((gt_x, gt_y))[align])
    aligned_xy = (rotation @ odom_xy.T).T + translation
    alignment_yaw = float(np.arctan2(rotation[1, 0], rotation[0, 0]))
    aligned_yaw = result.odom_yaw_rad.to_numpy(dtype=np.float64) + alignment_yaw
    position_error = np.linalg.norm(aligned_xy - np.column_stack((gt_x, gt_y)), axis=1)
    yaw_error = np.abs(wrap_angle(aligned_yaw - gt_yaw))

    future_index = np.searchsorted(stamps, stamps + horizon_s, side="left")
    has_future = future_index < len(result)
    future_index = np.minimum(future_index, len(result) - 1)
    future_position_error = position_error[future_index]
    future_yaw_error = yaw_error[future_index]
    future_lost = result.lost.to_numpy(dtype=bool)[future_index]
    lost_now = result.lost.to_numpy(dtype=bool)

    gt_xy = np.column_stack((gt_x, gt_y))
    gt_local_delta = rotate_global_delta_to_local(gt_xy[future_index] - gt_xy, gt_yaw)
    odom_local_delta = rotate_global_delta_to_local(
        aligned_xy[future_index] - aligned_xy, aligned_yaw
    )
    translation_rpe = np.linalg.norm(odom_local_delta - gt_local_delta, axis=1)
    rotation_rpe = np.abs(
        wrap_angle(
            (aligned_yaw[future_index] - aligned_yaw)
            - (gt_yaw[future_index] - gt_yaw)
        )
    )

    result["gt_x_m"] = gt_x
    result["gt_y_m"] = gt_y
    result["gt_yaw_rad"] = wrap_angle(gt_yaw)
    result["aligned_odom_x_m"] = aligned_xy[:, 0]
    result["aligned_odom_y_m"] = aligned_xy[:, 1]
    result["aligned_odom_yaw_rad"] = wrap_angle(aligned_yaw)
    result["position_error_m"] = position_error
    result["yaw_error_rad"] = yaw_error
    result["future_position_error_m"] = future_position_error
    result["future_position_error_growth_m"] = future_position_error - position_error
    result["future_yaw_error_rad"] = future_yaw_error
    result["future_lost"] = future_lost.astype(np.int8)
    result["future_new_lost"] = (future_lost & ~lost_now).astype(np.int8)
    result["future_error_growth_event"] = (
        (future_position_error - position_error) >= growth_threshold_m
    ).astype(np.int8)
    result["future_failure"] = ((future_position_error >= failure_position_m) | future_lost).astype(np.int8)
    result["has_future_label"] = has_future.astype(np.int8)
    result["future_translation_rpe_m"] = translation_rpe
    result["future_rotation_rpe_rad"] = rotation_rpe
    result["future_rpe_event"] = (
        (translation_rpe >= rpe_threshold_m) | (future_lost & ~lost_now)
    ).astype(np.int8)
    result["eligible_prediction"] = (has_future & ~lost_now).astype(np.int8)
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--health-csv", type=Path, required=True)
    parser.add_argument("--ground-truth", type=Path, required=True)
    parser.add_argument("--sequence", type=int, default=1)
    parser.add_argument("--horizon-s", type=float, default=1.0)
    parser.add_argument("--alignment-s", type=float, default=15.0)
    parser.add_argument("--failure-position-m", type=float, default=0.30)
    parser.add_argument("--growth-threshold-m", type=float, default=0.05)
    parser.add_argument("--rpe-threshold-m", type=float, default=0.05)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    health = pd.read_csv(args.health_csv)
    ground_truth = read_openloris_ground_truth(args.ground_truth, args.sequence)
    labeled = label_dataframe(
        health,
        ground_truth,
        args.horizon_s,
        args.alignment_s,
        args.failure_position_m,
        args.growth_threshold_m,
        args.rpe_threshold_m,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    labeled.to_csv(args.output, index=False)
    valid = labeled[labeled.has_future_label == 1]
    print(
        f"rows={len(labeled)} future_rows={len(valid)} "
        f"mean_position_error_m={valid.position_error_m.mean():.4f} "
        f"future_failures={int(valid.future_failure.sum())}"
    )


if __name__ == "__main__":
    main()
