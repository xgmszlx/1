# Implementation-base audit

Audited: 2026-08-13. Repositories are shallow snapshots used for source inspection. Commit hashes make the conclusions reproducible.

## Preferred components

### RTAB-Map ROS2

- Repository: `introlab/rtabmap_ros`, ROS2 branch, commit `16f6f05d70b299b2856b777c1a3db4ca0256fa6d` (2026-08-09 snapshot).
- License: BSD 3-Clause.
- ROS2 packages include RGB-D, stereo, ICP, odometry, SLAM, sync, examples, demos, and Nav2 integration.
- `rtabmap_odom` publishes both `odom_info` and `odom_info_lite` when subscribed.
- `rtabmap_msgs/OdomInfo` already exposes most of the proposed health inputs without a core fork:
  - `lost`, matches, inliers, features;
  - ICP inlier ratio, rotation, translation, structural complexity/distribution, correspondences;
  - a 6x6 covariance;
  - local visual/scan map sizes, key-frame and bundle statistics;
  - estimation time and key-frame-added status.
- `rtabmap_slam` publishes localization pose/covariance and `Info` contains loop-closure IDs, proximity IDs, posterior/likelihood, generic statistics, local path, current goal, and graph data.

Decision: this substantially reduces Candidate 1's code risk. Begin with an external ROS2 health-monitor node subscribing to existing messages. Avoid modifying RTAB-Map until an exposed field is proven insufficient.

### frontier_exploration_ros2

- Repository: `mertgulerx/frontier_exploration_ros2`, commit `ec530d2a813739cd25dd0c438d2365c510b9fad8` (2026-07-10 snapshot).
- License: Apache-2.0.
- Supports ROS2 Humble/Jazzy, Nav2 and SLAM Toolbox.
- The frontier search, policy, decision map, MRTSP ordering, suppression, and ROS node boundary are separated. Unit tests cover deterministic frontiers, map processing, ordering, preemption, control, and suppression.

Decision: preferred exploration engineering base. Add risk interfaces at the core-policy boundary instead of rewriting frontier extraction and Nav2 orchestration.

### ROS2 autonomous exploration benchmark

- Repository: `mertgulerx/autonomous-exploration-demo-benchmark`, commit `9dbf7bd869a9da5571c1b004a652e4b7988f348b` (2026-06-07 snapshot).
- License: Apache-2.0 at repository level; aggregated upstream components retain Apache/MIT/BSD licenses.
- ROS2 Jazzy + Gazebo Harmonic + Nav2 + SLAM Toolbox; Docker wrapper and Corridor, Bookstore and Warehouse worlds.
- Includes nearest/MRTSP frontier, m-explore-ros2, Nav2 wavefront and roadmap-explorer configurations, plus time/distance/CPU/RAM reporting.

Decision: preferred closed-loop scaffold. It is a young community benchmark, not a peer-reviewed scientific baseline, so add published baselines and independent metrics rather than citing its README performance as evidence.

### SLAM Toolbox

- Repository: `SteveMacenski/slam_toolbox`, ROS2 branch, commit `eee0cd5e4a161bb10f8334b5420c93876b31ca99` (2026-07-22 snapshot).
- License file: LGPL-2.1.
- Exposes scan-matching/loop-match response thresholds, localization pose covariance, pose graph publication, and loop-closure events.

Decision: stable 2-D LiDAR baseline and primary mapper for the initial Gazebo integration. Its public messages offer less modality detail than RTAB-Map, so the proposed cross-modal monitor should not depend only on SLAM Toolbox.

## Reference-only components

| Repository | Why useful | Why not the base |
|---|---|---|
| `suchetanrs/FIT-SLAM` | ROS2 Fisher-information path pruning, behavior-tree integration, Gazebo/ORB-SLAM3 launch design. | No explicit repository license; nested stack/submodules; 3-D traversability and visual-landmark assumptions. |
| `bairuofei/Graph-Based_SLAM-Aware_Exploration` | MIT-licensed equations/code for informative loop selection with a prior topo-metric graph. | ROS1 Stage/Karto/Concorde and prior-graph requirement. |
| `Seba-san/UncertaintyMap` | Equations/data organization for uncertainty frontiers and stopping. | No explicit license; README under construction; ROS1 and ad-hoc experimental scripts. |
| `JulioPlaced/ExplORB-SLAM` | Pose-graph spectral/optimality implementation ideas. | No explicit license, ROS1/ORB-SLAM2/Gazebo stack. |
| `efc-robot/Explore-Bench` | Benchmark taxonomy, historical maps, and exploration metrics. | ROS Melodic/Python 2.7; no explicit repository license; limited SLAM-accuracy metrics. |
| `HKUST-Aerial-Robotics/FALCON` | High-quality 3-D exploration evaluation and maps. | ROS1/UAV/3-D LiDAR/CUDA mismatch; no explicit license in repository metadata. |

## Environment blockers found

- Host: Ubuntu 20.04 with ROS Noetic only; no ROS2 installation was detected.
- A complete ROS Noetic RTAB-Map 0.21.13 stack, `rosbag`, and `cv_bridge` are already installed. This is sufficient for an offline OpenLORIS health-feature prototype and avoids making the ROS2 environment a prerequisite for the first scientific go/no-go test. The final integration still needs ROS2.
- No Docker or Podman executable was detected.
- Root filesystem has about 12 GB free.
- The chosen ROS2 benchmark expects Ubuntu 24.04/ROS2 Jazzy/Gazebo Harmonic, while FIT-SLAM 2 expects ROS2 Humble through Docker.
- OpenLORIS rosbag downloads are 6.7–16+ GB per grouped scene and about 95.6 GB total; decompressed bags can be roughly three times larger.

Implication: do not install ROS2 Jazzy or download a full OpenLORIS scene blindly on the current root partition. The Hugging Face tar index was inspected by HTTP range: the first member of the smallest 6.74 GB cafe archive is a 2,558,246,662-byte `cafe1-1.bag`, so that member can be fetched directly without storing the complete tar. Use ROS1 RTAB-Map for the offline gate; prefer a container or separate Ubuntu 22.04/24.04 environment for the later ROS2 closed loop.
