#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RESEARCH_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
BAG="${1:-$RESEARCH_DIR/data/openloris/cafe1-1.bag}"
PREFIX="${2:-cafe1-1}"

if [[ ! -f "$BAG" ]]; then
  echo "Missing bag: $BAG" >&2
  exit 1
fi

source /opt/ros/noetic/setup.bash
if ! rosparam get /rosversion >/dev/null 2>&1; then
  echo "roscore is not running. Start it before this script." >&2
  exit 1
fi
rosparam set /use_sim_time true
mkdir -p "$SCRIPT_DIR/results"

cleanup() {
  kill "${VIS_RECORDER_PID:-}" "${LIDAR_RECORDER_PID:-}" \
    "${VIS_PID:-}" "${LIDAR_PID:-}" "${REPEATER_PID:-}" 2>/dev/null || true
  wait "${VIS_RECORDER_PID:-}" "${LIDAR_RECORDER_PID:-}" \
    "${VIS_PID:-}" "${LIDAR_PID:-}" "${REPEATER_PID:-}" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

/usr/bin/python3 "$SCRIPT_DIR/repeat_camera_info.py" &
REPEATER_PID=$!

rosrun rtabmap_odom rgbd_odometry \
  __ns:=/visual __name:=rgbd_odometry \
  rgb/image:=/d400/color/image_raw \
  depth/image:=/d400/aligned_depth_to_color/image_raw \
  rgb/camera_info:=/d400/color/camera_info_repeated \
  _frame_id:=base_link _odom_frame_id:=odom_visual _publish_tf:=false \
  _approx_sync:=true _approx_sync_max_interval:=0.05 \
  _sync_queue_size:=100 _topic_queue_size:=30 \
  _Vis/MinInliers:=12 &
VIS_PID=$!

rosrun rtabmap_odom icp_odometry \
  __ns:=/lidar __name:=icp_odometry \
  scan:=/scan \
  _frame_id:=base_link _odom_frame_id:=odom_lidar _publish_tf:=false \
  _scan_normal_k:=20 _Icp/PointToPlane:=true _Icp/VoxelSize:=0 \
  _Icp/MaxCorrespondenceDistance:=0.5 &
LIDAR_PID=$!

/usr/bin/python3 "$SCRIPT_DIR/extract_health_csv.py" \
  --output "$SCRIPT_DIR/results/${PREFIX}-visual-health.csv" \
  --node-name "${PREFIX//-/_}_visual_health_recorder" \
  --info-topic /visual/odom_info --odom-topic /visual/odom --scan-topic /scan &
VIS_RECORDER_PID=$!

/usr/bin/python3 "$SCRIPT_DIR/extract_health_csv.py" \
  --output "$SCRIPT_DIR/results/${PREFIX}-lidar-health.csv" \
  --node-name "${PREFIX//-/_}_lidar_health_recorder" \
  --info-topic /lidar/odom_info --odom-topic /lidar/odom --scan-topic /scan &
LIDAR_RECORDER_PID=$!

sleep 2
rosbag play --clock --rate 0.25 --delay 2 --quiet "$BAG"
sleep 2

for mode in visual lidar; do
  output="$SCRIPT_DIR/results/${PREFIX}-${mode}-health.csv"
  rows=$(wc -l < "$output")
  if [[ "$rows" -le 10 ]]; then
    echo "$mode extraction failed: only $rows CSV lines." >&2
    exit 1
  fi
  echo "$mode extraction complete: $rows CSV lines at $output"
done
