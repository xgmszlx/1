#!/usr/bin/env python3
"""Record online-available RTAB-Map/LaserScan health features to CSV.

Ground truth is intentionally absent from this node. Labels are joined offline
to prevent accidental future/ground-truth leakage into the online feature path.
"""

from __future__ import annotations

import argparse
import csv
import math
from pathlib import Path
import threading

import numpy as np
import rospy
from nav_msgs.msg import Odometry
from rtabmap_msgs.msg import OdomInfo
from sensor_msgs.msg import LaserScan


FIELDS = [
    "stamp",
    "lost",
    "matches",
    "inliers",
    "visual_inlier_ratio",
    "features",
    "icp_inliers_ratio",
    "icp_rotation",
    "icp_translation",
    "icp_structural_complexity",
    "icp_structural_distribution",
    "icp_correspondences",
    "cov_trace_xyyaw",
    "local_map_size",
    "local_scan_map_size",
    "estimation_time_s",
    "distance_travelled_m",
    "scan_valid_ratio",
    "scan_range_mean_m",
    "scan_range_std_m",
    "odom_x_m",
    "odom_y_m",
    "odom_yaw_rad",
]


def quaternion_to_yaw(x: float, y: float, z: float, w: float) -> float:
    return math.atan2(2.0 * (w * z + x * y), 1.0 - 2.0 * (y * y + z * z))


class HealthRecorder:
    def __init__(self, output: Path, info_topic: str, odom_topic: str, scan_topic: str) -> None:
        output.parent.mkdir(parents=True, exist_ok=True)
        self._handle = output.open("w", newline="", encoding="utf-8")
        self._writer = csv.DictWriter(self._handle, fieldnames=FIELDS)
        self._writer.writeheader()
        self._lock = threading.Lock()
        self._scan = (math.nan, math.nan, math.nan)
        self._pose = (math.nan, math.nan, math.nan)
        self._rows = 0
        rospy.Subscriber(scan_topic, LaserScan, self._scan_callback, queue_size=10)
        rospy.Subscriber(odom_topic, Odometry, self._odom_callback, queue_size=20)
        rospy.Subscriber(info_topic, OdomInfo, self._info_callback, queue_size=100)
        rospy.on_shutdown(self.close)

    def _scan_callback(self, message: LaserScan) -> None:
        values = np.asarray(message.ranges, dtype=np.float64)
        finite = np.isfinite(values)
        valid = np.zeros(values.shape, dtype=bool)
        valid[finite] = (values[finite] >= message.range_min) & (values[finite] <= message.range_max)
        if np.any(valid):
            stats = (float(np.mean(valid)), float(np.mean(values[valid])), float(np.std(values[valid])))
        else:
            stats = (0.0, math.nan, math.nan)
        with self._lock:
            self._scan = stats

    def _odom_callback(self, message: Odometry) -> None:
        p = message.pose.pose.position
        q = message.pose.pose.orientation
        pose = (float(p.x), float(p.y), quaternion_to_yaw(q.x, q.y, q.z, q.w))
        with self._lock:
            self._pose = pose

    def _info_callback(self, message: OdomInfo) -> None:
        covariance = np.asarray(message.covariance, dtype=np.float64).reshape(6, 6)
        with self._lock:
            scan = self._scan
            pose = self._pose
        row = {
            "stamp": message.header.stamp.to_sec(),
            "lost": int(message.lost),
            "matches": message.matches,
            "inliers": message.inliers,
            "visual_inlier_ratio": message.inliers / max(message.matches, 1),
            "features": message.features,
            "icp_inliers_ratio": message.icpInliersRatio,
            "icp_rotation": message.icpRotation,
            "icp_translation": message.icpTranslation,
            "icp_structural_complexity": message.icpStructuralComplexity,
            "icp_structural_distribution": message.icpStructuralDistribution,
            "icp_correspondences": message.icpCorrespondences,
            "cov_trace_xyyaw": covariance[0, 0] + covariance[1, 1] + covariance[5, 5],
            "local_map_size": message.localMapSize,
            "local_scan_map_size": message.localScanMapSize,
            "estimation_time_s": message.timeEstimation,
            "distance_travelled_m": message.distanceTravelled,
            "scan_valid_ratio": scan[0],
            "scan_range_mean_m": scan[1],
            "scan_range_std_m": scan[2],
            "odom_x_m": pose[0],
            "odom_y_m": pose[1],
            "odom_yaw_rad": pose[2],
        }
        self._writer.writerow(row)
        self._rows += 1
        if self._rows % 50 == 0:
            self._handle.flush()

    def close(self) -> None:
        if not self._handle.closed:
            self._handle.flush()
            self._handle.close()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--info-topic", default="/rtabmap/odom_info")
    parser.add_argument("--odom-topic", default="/rtabmap/odom")
    parser.add_argument("--scan-topic", default="/scan")
    parser.add_argument("--node-name", default="openloris_health_recorder")
    args, ros_args = parser.parse_known_args()
    rospy.init_node(args.node_name, argv=["extract_health_csv.py", *ros_args])
    HealthRecorder(args.output, args.info_topic, args.odom_topic, args.scan_topic)
    rospy.spin()


if __name__ == "__main__":
    main()
