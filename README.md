# 主动 SLAM 选题收敛与最小验证

本仓库记录一项仍在进行中的主动 SLAM 研究选题工作。目标是在真实文献、公开代码、公开数据和可否证实验的约束下，为低成本室内轮式机器人收敛一个可实现、具备 SCI 二区/三区投稿潜力的研究问题。

> 当前结论不是“方法已经有效”。合成闭环支持“恢复必须受额外路径预算约束”，但第一条 OpenLORIS 真实序列没有证明 RGB-D 与二维激光健康特征的简单融合优于视觉或 covariance 基线。因此跨模态方法题目前为黄灯，等待独立模态与跨场景验证。

## 研究条件

- 平台：四轮室内机器人；RGB-D 相机、二维激光雷达、IMU；预计迁移到 ROS 2。
- 工程约束：优先轻量模型与模块化开源系统，不选择端到端强化学习作为第一篇论文路线。
- 证据约束：主要结论必须由同行评审论文、官方仓库与公开数据支撑。
- 验证约束：公开数据验证健康信号，公开仿真环境验证主动闭环；自采数据只作最终演示。

## 当前候选题

### 条件式方法题

**面向定位退化的预算约束主动 SLAM 避险与选择性恢复**

研究问题：仅使用当前及历史的 RGB-D 跟踪、二维激光扫描匹配和估计器不确定性，能否在未见场景中校准未来短时定位退化概率，并在显式额外路径预算下改善主动探索的轨迹与地图质量？

如果后续独立模态实验证明视觉和二维激光确实存在稳定互补性，题目再恢复为：

**Calibrated Selective Recovery for Active RGB-D–2D-LiDAR SLAM under Complementary Degradation**

### 回退题

**互补视觉–激光退化下的可复现 ROS 2 主动 SLAM 基准与失败感知基线**

该方向也不是自动成立：必须证明真实约束的退化会改变多个探索策略或 SLAM 后端的排名/失效模式，否则只属于普通工程集成。

## 已完成工作

1. 建立可复现的文献检索协议、证据矩阵和核验 BibTeX；
2. 审计 RTAB-Map、SLAM Toolbox、frontier exploration、FIT-SLAM 与公开 ROS 2 exploration benchmark；
3. 在公开 Corridor 几何上完成轻量闭环机制实验；
4. 完成 OpenLORIS `cafe1-1` 的 RTAB-Map RGB-D + 二维激光 ICP 全序列回放；
5. 建立不读取在线真值的健康特征记录器，以及离线 GT 对齐、未来 RPE 标签、因果时间窗和时间外推评估；
6. 将不支持原假设的结果保留为选题淘汰证据。

## 关键阶段结果

### 合成闭环（只用于机制排错）

在固定 16 m 累积恢复预算后，共同退化条件下，相对 distance-advantage 基线：

- 路径由 56.50 m 增至 61.50 m，开销 8.85%；
- 合成 pose-RMSE 由 0.4886 m 降至 0.3791 m；
- 失败事件由 3.3 次降至 1.9 次；
- 单视觉退化下没有错误回访。

这些结果不能被表述为真实 SLAM 性能。

### OpenLORIS `cafe1-1`（真实数据模块门）

采用时间前 60% 训练、1 s embargo、后段测试，以未来 1 s translation RPE 超过 0.05 m或新发生 lost 为事件：

| 特征模型 | AUROC | AUPRC | Brier | ECE-10 |
|---|---:|---:|---:|---:|
| 视觉-only | 0.6380 | 0.8293 | **0.2098** | **0.1038** |
| covariance 时间窗 | **0.6702** | **0.8470** | 0.2374 | 0.1931 |
| 瞬时跨模态 | 0.6125 | 0.8299 | 0.2812 | 0.2260 |
| 跨模态时间窗 | 0.4612 | 0.6884 | 0.4778 | 0.4775 |

同一序列的时间外推仍不是跨场景证据。当前结果支持视觉/covariance 预警的可行性，但不支持简单跨模态融合。

## 目录

- `literature/`：检索协议、证据矩阵、核验参考文献；
- `reports/`：候选排序、阶段报告、Go/No-Go 判决；
- `experiments/minimal_closed_loop/`：合成闭环机制实验；
- `experiments/openloris_health/`：ROS 1/RTAB-Map 离线健康信号实验；
- `projects/implementation_audit.md`：开源实现与许可证审计；
- `projects/autonomous-exploration-demo-benchmark/`：固定版本的公开 Corridor 来源（Git submodule）；
- `projects/openloris-scene-tools/`：OpenLORIS 官方工具和真值（Git submodule）。

## 快速复现

```bash
git clone --recurse-submodules git@github.com:xgmszlx/1.git
cd 1
python -m pip install -r requirements.txt
pytest -q experiments/minimal_closed_loop/test_simulator.py \
  experiments/openloris_health/test_label_health_csv.py \
  experiments/openloris_health/test_causal_window_features.py
```

重跑合成主实验：

```bash
python experiments/minimal_closed_loop/run_experiment.py \
  --seeds 10 --recovery-budget-m 16 \
  --output experiments/minimal_closed_loop/results_budgeted/main_10seeds
```

OpenLORIS 数据集采用 CC BY-ND 4.0，本仓库不分发 rosbag、数据库、逐帧派生 CSV 或修改后的数据。取得原始数据并安装 ROS Noetic + RTAB-Map 后，按 `experiments/openloris_health/README.md` 执行。

## 重要边界

- `reports/` 中的题名和创新点均为暂定研究判断，不是已发表结论；
- `FULLTEXT_VERIFIED`、`ABSTRACT_VERIFIED`、`CODE_VERIFIED` 等标签的含义见文献证据矩阵；
- 未通过跨场景与闭环门槛前，不开发完整 ROS 2 方法节点；
- 使用 AI 辅助进行了检索组织、代码实现和分析，引用与研究判断仍需作者人工复核。
