#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RESEARCH_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
BAG="$RESEARCH_DIR/data/openloris/cafe1-1.bag"
OUTPUT="$SCRIPT_DIR/results/cafe1-1-health.csv"
EXPECTED_BYTES=2558246662

if [[ ! -f "$BAG" ]]; then
  echo "Missing bag: $BAG" >&2
  exit 1
fi
if [[ "$(stat -c '%s' "$BAG")" -ne "$EXPECTED_BYTES" ]]; then
  echo "Bag size check failed; expected $EXPECTED_BYTES bytes." >&2
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
  kill "${RECORDER_PID:-}" "${ODOM_PID:-}" "${REPEATER_PID:-}" 2>/dev/null || true
  wait "${RECORDER_PID:-}" "${ODOM_PID:-}" "${REPEATER_PID:-}" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

/usr/bin/python3 "$SCRIPT_DIR/repeat_camera_info.py" &
REPEATER_PID=$!

rosrun rtabmap_odom rgbdicp_odometry \
  __ns:=/rtabmap __name:=rgbdicp_odometry \
  rgb/image:=/d400/color/image_raw \
  depth/image:=/d400/aligned_depth_to_color/image_raw \
  rgb/camera_info:=/d400/color/camera_info_repeated \
  scan:=/scan \
  _frame_id:=base_link _odom_frame_id:=odom_rtabmap _publish_tf:=false \
  _subscribe_scan:=true _subscribe_scan_cloud:=false \
  _approx_sync:=true _approx_sync_max_interval:=0.05 \
  _sync_queue_size:=100 _topic_queue_size:=30 _scan_normal_k:=20 \
  _Reg/Strategy:=2 _Vis/MinInliers:=12 \
  _Icp/PointToPlane:=true _Icp/VoxelSize:=0 \
  _Icp/MaxCorrespondenceDistance:=0.5 &
ODOM_PID=$!

/usr/bin/python3 "$SCRIPT_DIR/extract_health_csv.py" \
  --output "$OUTPUT" \
  --info-topic /rtabmap/odom_info \
  --odom-topic /rtabmap/odom \
  --scan-topic /scan &
RECORDER_PID=$!

sleep 2
rosbag play --clock --rate 0.25 --delay 2 --quiet "$BAG"
sleep 2

ROWS=$(wc -l < "$OUTPUT")
if [[ "$ROWS" -le 10 ]]; then
  echo "Health extraction failed: only $ROWS CSV lines." >&2
  exit 1
fi
echo "Health extraction complete: $ROWS CSV lines at $OUTPUT"
