from pathlib import Path

import numpy as np

from simulator import (
    FREE,
    UNKNOWN,
    SimConfig,
    bfs_tree,
    frontier_candidates,
    fused_risk_map,
    lidar_health_map,
    load_sdf_box_world,
    reconstruct_path,
    reveal_scan,
    run_simulation,
    visual_health_map,
)


ROOT = Path(__file__).resolve().parents[2]
SDF = ROOT / "projects/autonomous-exploration-demo-benchmark/simulation/worlds/corridor/corridor.world"


def test_world_and_frontiers_are_reachable():
    world = load_sdf_box_world(SDF)
    start = world.world_to_grid(0.0, 0.0)
    assert world.occupancy[start] == FREE
    belief = np.full(world.occupancy.shape, UNKNOWN, dtype=np.int8)
    reveal_scan(world, belief, start, SimConfig(ray_count=90))
    candidates = frontier_candidates(belief, start, 1)
    assert candidates
    distances, parent = bfs_tree(belief == FREE, start)
    path = reconstruct_path(parent, start, candidates[0])
    assert path[0] == start and path[-1] == candidates[0]
    assert distances[candidates[0]] == len(path) - 1


def test_cross_modal_fusion_compensates_single_visual_failure():
    world = load_sdf_box_world(SDF)
    visual = visual_health_map(world, "visual_degradation")
    lidar = lidar_health_map(world, rays=48)
    risk = fused_risk_map(world, visual, lidar, "visual_degradation")
    free = world.occupancy == FREE
    low_visual = free & (visual < 0.2)
    assert np.any(low_visual)
    # Some low-texture cells remain tolerable when laser geometry is informative.
    assert np.any(low_visual & (lidar > 0.35) & (risk < 0.75))


def test_short_run_is_deterministic():
    world = load_sdf_box_world(SDF)
    cfg = SimConfig(max_steps=120, ray_count=72, coverage_target=0.99)
    visual = visual_health_map(world, "complementary")
    lidar = lidar_health_map(world, rays=48)
    health = (visual, lidar, fused_risk_map(world, visual, lidar, "complementary"))
    a = run_simulation(world, "nearest", 3, "complementary", cfg, health)
    b = run_simulation(world, "nearest", 3, "complementary", cfg, health)
    assert a.as_dict() == b.as_dict()
    assert a.path_m > 0


def test_zero_recovery_budget_prevents_stabilization():
    world = load_sdf_box_world(SDF)
    cfg = SimConfig(recovery_detour_budget_m=0.0)
    visual = visual_health_map(world, "common_mode")
    lidar = lidar_health_map(world, rays=48)
    health = (visual, lidar, fused_risk_map(world, visual, lidar, "common_mode"))
    result = run_simulation(world, "cross_modal_risk", 0, "common_mode", cfg, health)
    assert result.stabilization_revisits == 0
    assert result.recovery_budget_spent_m == 0.0
