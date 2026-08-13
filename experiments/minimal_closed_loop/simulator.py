from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from pathlib import Path
import math
import xml.etree.ElementTree as ET

import numpy as np
from scipy import ndimage
from skimage.draw import line


UNKNOWN = np.int8(-1)
FREE = np.int8(0)
OCCUPIED = np.int8(1)


@dataclass(frozen=True)
class GridWorld:
    occupancy: np.ndarray
    resolution: float
    x_min: float
    y_min: float

    def world_to_grid(self, x: float, y: float) -> tuple[int, int]:
        return (
            int(round((y - self.y_min) / self.resolution)),
            int(round((x - self.x_min) / self.resolution)),
        )

    def grid_to_world(self, cell: tuple[int, int]) -> tuple[float, float]:
        r, c = cell
        return self.x_min + c * self.resolution, self.y_min + r * self.resolution


@dataclass
class SimConfig:
    sensor_range_m: float = 4.5
    ray_count: int = 360
    coverage_target: float = 0.985
    max_steps: int = 4500
    min_frontier_cluster: int = 2
    visual_risk_weight: float = 2.0
    cross_modal_risk_weight: float = 2.2
    stabilization_threshold: float = 0.75
    stabilization_risk_gate: float = 0.45
    stabilization_cooldown: int = 35
    recovery_detour_budget_m: float = 16.0
    anchor_stride: int = 16
    failure_error_m: float = 0.55
    base_step_variance: float = 2.0e-5
    process_scale: float = 3.5e-3


@dataclass
class SimResult:
    policy: str
    seed: int
    complete: bool
    coverage: float
    path_m: float
    steps: int
    pose_rmse_m: float
    max_pose_error_m: float
    risk_exposure: float
    failure_steps: int
    stabilization_revisits: int
    recovery_budget_spent_m: float
    decision_count: int
    trajectory: list[tuple[int, int]] = field(repr=False)

    def as_dict(self) -> dict:
        d = self.__dict__.copy()
        d.pop("trajectory")
        return d


def load_sdf_box_world(path: str | Path, resolution: float = 0.25) -> GridWorld:
    """Rasterize collision boxes from the benchmark's planar SDF world."""
    root = ET.parse(path).getroot()
    floor_size = None
    for model in root.iter("model"):
        if model.attrib.get("name") == "floor":
            size = model.find("./link/collision/geometry/box/size")
            if size is not None:
                floor_size = [float(v) for v in size.text.split()]
                break
    if floor_size is None:
        raise ValueError("floor collision box not found")

    width, height = floor_size[:2]
    x_min, y_min = -width / 2.0, -height / 2.0
    cols = int(round(width / resolution)) + 1
    rows = int(round(height / resolution)) + 1
    grid = np.zeros((rows, cols), dtype=np.int8)
    grid[[0, -1], :] = OCCUPIED
    grid[:, [0, -1]] = OCCUPIED

    for model in root.iter("model"):
        if model.attrib.get("name") in {"floor"}:
            continue
        for link_node in model.findall("link"):
            pose_node = link_node.find("pose")
            collision = link_node.find("collision")
            if pose_node is None or collision is None:
                continue
            size_node = collision.find("./geometry/box/size")
            if size_node is None:
                continue
            pose = [float(v) for v in pose_node.text.split()]
            size = [float(v) for v in size_node.text.split()]
            x, y, yaw = pose[0], pose[1], pose[5]
            sx, sy = size[0], size[1]
            radius = math.hypot(sx, sy) / 2.0 + resolution
            r0, c0 = int((y - radius - y_min) / resolution), int((x - radius - x_min) / resolution)
            r1, c1 = int((y + radius - y_min) / resolution) + 1, int((x + radius - x_min) / resolution) + 1
            co, si = math.cos(yaw), math.sin(yaw)
            for r in range(max(0, r0), min(rows, r1)):
                for c in range(max(0, c0), min(cols, c1)):
                    wx, wy = x_min + c * resolution, y_min + r * resolution
                    dx, dy = wx - x, wy - y
                    lx, ly = co * dx + si * dy, -si * dx + co * dy
                    if abs(lx) <= sx / 2.0 + resolution * 0.48 and abs(ly) <= sy / 2.0 + resolution * 0.48:
                        grid[r, c] = OCCUPIED
    return GridWorld(grid, resolution, x_min, y_min)


def _neighbors4(cell: tuple[int, int], shape: tuple[int, int]):
    r, c = cell
    for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
        rr, cc = r + dr, c + dc
        if 0 <= rr < shape[0] and 0 <= cc < shape[1]:
            yield rr, cc


def reveal_scan(world: GridWorld, belief: np.ndarray, cell: tuple[int, int], cfg: SimConfig) -> None:
    radius_cells = cfg.sensor_range_m / world.resolution
    r0, c0 = cell
    belief[r0, c0] = world.occupancy[r0, c0]
    for angle in np.linspace(0.0, 2.0 * math.pi, cfg.ray_count, endpoint=False):
        rr = int(round(r0 + radius_cells * math.sin(angle)))
        cc = int(round(c0 + radius_cells * math.cos(angle)))
        rr = min(max(rr, 0), world.occupancy.shape[0] - 1)
        cc = min(max(cc, 0), world.occupancy.shape[1] - 1)
        for r, c in zip(*line(r0, c0, rr, cc)):
            belief[r, c] = world.occupancy[r, c]
            if world.occupancy[r, c] == OCCUPIED:
                break


def frontier_mask(belief: np.ndarray) -> np.ndarray:
    unknown = belief == UNKNOWN
    adjacent_unknown = ndimage.binary_dilation(unknown, structure=np.array([[0, 1, 0], [1, 1, 1], [0, 1, 0]]))
    return (belief == FREE) & adjacent_unknown


def bfs_tree(free: np.ndarray, start: tuple[int, int]) -> tuple[np.ndarray, np.ndarray]:
    distances = np.full(free.shape, -1, dtype=np.int32)
    parent = np.full((*free.shape, 2), -1, dtype=np.int16)
    if not free[start]:
        return distances, parent
    q = deque([start])
    distances[start] = 0
    while q:
        cur = q.popleft()
        for nxt in _neighbors4(cur, free.shape):
            if free[nxt] and distances[nxt] < 0:
                distances[nxt] = distances[cur] + 1
                parent[nxt] = cur
                q.append(nxt)
    return distances, parent


def reconstruct_path(parent: np.ndarray, start: tuple[int, int], goal: tuple[int, int]) -> list[tuple[int, int]]:
    if goal == start:
        return [start]
    if parent[goal][0] < 0:
        return []
    path = [goal]
    cur = goal
    while cur != start:
        p = parent[cur]
        cur = int(p[0]), int(p[1])
        path.append(cur)
    path.reverse()
    return path


def frontier_candidates(belief: np.ndarray, current: tuple[int, int], min_size: int) -> list[tuple[int, int]]:
    mask = frontier_mask(belief)
    labels, count = ndimage.label(mask, structure=np.ones((3, 3), dtype=np.int8))
    dist, _ = bfs_tree(belief == FREE, current)
    candidates = []
    for label_id in range(1, count + 1):
        cells = np.argwhere(labels == label_id)
        if len(cells) < min_size:
            continue
        reachable = [(int(r), int(c)) for r, c in cells if dist[r, c] >= 0]
        if reachable:
            candidates.append(min(reachable, key=lambda x: dist[x]))
    return candidates


def predicted_gain(belief: np.ndarray, goal: tuple[int, int], radius_cells: int) -> int:
    r, c = goal
    r0, r1 = max(0, r - radius_cells), min(belief.shape[0], r + radius_cells + 1)
    c0, c1 = max(0, c - radius_cells), min(belief.shape[1], c + radius_cells + 1)
    yy, xx = np.ogrid[r0:r1, c0:c1]
    disk = (yy - r) ** 2 + (xx - c) ** 2 <= radius_cells**2
    return int(np.count_nonzero((belief[r0:r1, c0:c1] == UNKNOWN) & disk))


def distance_advantage(belief: np.ndarray, current: tuple[int, int], goal: tuple[int, int], current_distance: int) -> float:
    free = belief == FREE
    distances, _ = bfs_tree(free, goal)
    reachable = distances >= 0
    if not np.any(reachable):
        return -float("inf")
    return float(np.mean(distances[reachable]) - current_distance)


def _surface_normals(occupancy: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    signed = ndimage.distance_transform_edt(occupancy == FREE)
    gy, gx = np.gradient(signed)
    norm = np.hypot(gx, gy)
    norm[norm < 1e-6] = 1.0
    return gx / norm, gy / norm


def lidar_health_map(world: GridWorld, range_m: float = 4.5, rays: int = 96) -> np.ndarray:
    """Approximate 2-D scan-matching observability using a local point-to-line Hessian."""
    occ = world.occupancy
    nx, ny = _surface_normals(occ)
    radius_cells = range_m / world.resolution
    result = np.zeros(occ.shape, dtype=np.float64)
    angles = np.linspace(0.0, 2.0 * math.pi, rays, endpoint=False)
    free_cells = np.argwhere(occ == FREE)
    for r0, c0 in free_cells:
        hessian = np.zeros((3, 3), dtype=np.float64)
        hit_count = 0
        for angle in angles:
            rr = int(round(r0 + radius_cells * math.sin(angle)))
            cc = int(round(c0 + radius_cells * math.cos(angle)))
            rr = min(max(rr, 0), occ.shape[0] - 1)
            cc = min(max(cc, 0), occ.shape[1] - 1)
            for r, c in zip(*line(r0, c0, rr, cc)):
                if occ[r, c] == OCCUPIED:
                    px, py = (c - c0) * world.resolution, (r - r0) * world.resolution
                    normal = np.array([nx[r, c], ny[r, c]])
                    jac = np.array([normal[0], normal[1], -normal[0] * py + normal[1] * px])
                    hessian += np.outer(jac, jac)
                    hit_count += 1
                    break
        if hit_count >= 8:
            eig = np.linalg.eigvalsh(hessian / hit_count)
            result[r0, c0] = float(np.clip(eig[0] / (eig[-1] + 1e-9) * 12.0, 0.0, 1.0))
    return ndimage.gaussian_filter(result, 0.7)


def visual_health_map(world: GridWorld, scenario: str) -> np.ndarray:
    """Deterministic feature-density proxy; regions are explicit so the trial is auditable."""
    result = np.full(world.occupancy.shape, 0.82, dtype=np.float64)
    for r, c in np.argwhere(world.occupancy == FREE):
        x, y = world.grid_to_world((int(r), int(c)))
        texture = 0.82
        if scenario in {"visual_degradation", "complementary", "common_mode"}:
            if -3.2 <= x <= 3.2 and -2.1 <= y <= 2.1:
                texture = 0.12
            elif 3.0 <= x <= 6.2 and 2.0 <= y <= 6.6:
                texture = 0.28
        # A small deterministic spatial variation avoids artificial score ties.
        result[r, c] = np.clip(texture + 0.08 * math.sin(0.7 * x + 0.3 * y), 0.05, 0.98)
    return result


def fused_risk_map(world: GridWorld, visual: np.ndarray, lidar: np.ndarray, scenario: str) -> np.ndarray:
    # Each modality gets worse continuously as its health falls. Information-form
    # fusion means one healthy modality can compensate for the other.
    var_v = 0.15 + 2.8 * (1.0 - visual) ** 2
    var_l = 0.12 + 2.4 * (1.0 - lidar) ** 2
    fused = 1.0 / (1.0 / var_v + 1.0 / var_l)
    if scenario == "common_mode":
        for r, c in np.argwhere(world.occupancy == FREE):
            x, y = world.grid_to_world((int(r), int(c)))
            if -2.2 <= x <= 2.2 and -2.1 <= y <= 2.1:
                fused[r, c] += 1.1
    free = world.occupancy == FREE
    # Use one fixed calibration scale across scenarios. Per-map min/max or
    # percentile normalization would manufacture "high risk" even when every
    # cell is healthy, making cross-scenario thresholds meaningless.
    risk = np.clip(fused / 0.60, 0.0, 1.0)
    risk[~free] = 1.0
    return risk


def _path_mean(field: np.ndarray, path: list[tuple[int, int]]) -> float:
    return float(np.mean([field[p] for p in path])) if path else float("inf")


def choose_frontier(
    policy: str,
    world: GridWorld,
    belief: np.ndarray,
    current: tuple[int, int],
    candidates: list[tuple[int, int]],
    visual: np.ndarray,
    risk: np.ndarray,
    cfg: SimConfig,
) -> tuple[tuple[int, int], list[tuple[int, int]]]:
    distances, parent = bfs_tree(belief == FREE, current)
    rows = []
    radius_cells = int(round(cfg.sensor_range_m / world.resolution))
    for goal in candidates:
        d = int(distances[goal])
        if d < 0:
            continue
        path = reconstruct_path(parent, current, goal)
        da = distance_advantage(belief, current, goal, d)
        gain = predicted_gain(belief, goal, radius_cells)
        rows.append({"goal": goal, "path": path, "d": d, "da": da, "gain": gain})
    if not rows:
        raise RuntimeError("no reachable frontier")

    if policy == "nearest":
        selected = min(rows, key=lambda x: (x["d"], -x["gain"]))
    elif policy == "information_gain":
        selected = max(rows, key=lambda x: 3.0 * math.log1p(x["gain"]) - x["d"])
    elif policy == "distance_advantage":
        selected = max(rows, key=lambda x: x["da"])
    else:
        da_values = np.array([x["da"] for x in rows])
        da_scale = float(np.std(da_values)) + 1e-6
        for row in rows:
            row["da_z"] = (row["da"] - float(np.mean(da_values))) / da_scale
        if policy == "visual_risk":
            selected = max(rows, key=lambda x: x["da_z"] - cfg.visual_risk_weight * _path_mean(1.0 - visual, x["path"]))
        elif policy == "cross_modal_risk":
            selected = max(rows, key=lambda x: x["da_z"] - cfg.cross_modal_risk_weight * _path_mean(risk, x["path"]))
        else:
            raise ValueError(f"unknown policy: {policy}")
    return selected["goal"], selected["path"]


def run_simulation(
    world: GridWorld,
    policy: str,
    seed: int,
    scenario: str = "complementary",
    cfg: SimConfig | None = None,
    health_maps: tuple[np.ndarray, np.ndarray, np.ndarray] | None = None,
) -> SimResult:
    cfg = cfg or SimConfig()
    rng = np.random.default_rng(seed)
    belief = np.full(world.occupancy.shape, UNKNOWN, dtype=np.int8)
    start = world.world_to_grid(0.0, 0.0)
    if world.occupancy[start] != FREE:
        free = np.argwhere(world.occupancy == FREE)
        start = tuple(int(v) for v in free[np.argmin(np.sum((free - np.array(start)) ** 2, axis=1))])
    current = start
    if health_maps is None:
        visual = visual_health_map(world, scenario)
        lidar = lidar_health_map(world, cfg.sensor_range_m)
        risk = fused_risk_map(world, visual, lidar, scenario)
    else:
        visual, lidar, risk = health_maps
    reveal_scan(world, belief, current, cfg)

    trajectory = [current]
    error = np.zeros(2, dtype=np.float64)
    errors = [0.0]
    uncertainty = 0.0
    risk_exposure = 0.0
    failures = 0
    in_failure = False
    decisions = 0
    stabilizations = 0
    recovery_budget_spent_m = 0.0
    last_stabilization = -cfg.stabilization_cooldown
    anchors = [start]
    # The SDF floor also contains free cells outside the enclosed wall layout.
    # Only the connected component containing the robot is physically reachable.
    reachable_true, _ = bfs_tree(world.occupancy == FREE, start)
    reachable_free = reachable_true >= 0
    free_total = int(np.count_nonzero(reachable_free))

    def coverage() -> float:
        return float(np.count_nonzero((belief == FREE) & reachable_free) / free_total)

    while len(trajectory) - 1 < cfg.max_steps and coverage() < cfg.coverage_target:
        # Event-triggered revisit is only part of the proposed cross-modal policy.
        if (
            policy == "cross_modal_risk"
            and uncertainty > cfg.stabilization_threshold
            and risk[current] > cfg.stabilization_risk_gate
            and len(trajectory) - 1 - last_stabilization >= cfg.stabilization_cooldown
        ):
            distances, parent = bfs_tree(belief == FREE, current)
            valid = []
            for anchor_candidate in anchors:
                distance_cells = int(distances[anchor_candidate])
                # A revisit normally has to be paid for twice: travel back to a
                # stable anchor and later regain exploration progress. This is
                # a conservative detour estimate, not a claimed optimal bound.
                estimated_detour_m = 2.0 * distance_cells * world.resolution
                if (
                    distance_cells > 3
                    and risk[anchor_candidate] < 0.45
                    and recovery_budget_spent_m + estimated_detour_m <= cfg.recovery_detour_budget_m
                ):
                    valid.append(anchor_candidate)
            if valid:
                anchor = min(valid, key=lambda a: distances[a] / max(visual[a] + (1.0 - risk[a]), 0.1))
                path = reconstruct_path(parent, current, anchor)
                goal = anchor
                planned_recovery_cost_m = 2.0 * int(distances[anchor]) * world.resolution
                is_stabilization = True
            else:
                is_stabilization = False
        else:
            is_stabilization = False

        if not is_stabilization:
            candidates = frontier_candidates(belief, current, cfg.min_frontier_cluster)
            if not candidates:
                break
            goal, path = choose_frontier(policy, world, belief, current, candidates, visual, risk, cfg)
        decisions += 1

        for nxt in path[1:]:
            current = nxt
            trajectory.append(current)
            local_risk = float(risk[current])
            risk_exposure += local_risk
            q = cfg.base_step_variance + cfg.process_scale * local_risk**2
            error += rng.normal(0.0, math.sqrt(q), size=2)
            uncertainty += q * 28.0
            err_norm = float(np.linalg.norm(error))
            errors.append(err_norm)
            now_failure = err_norm > cfg.failure_error_m
            if now_failure and not in_failure:
                failures += 1
            in_failure = now_failure
            reveal_scan(world, belief, current, cfg)
            if len(trajectory) - 1 >= cfg.max_steps:
                break

        if is_stabilization and current == goal:
            recovery_budget_spent_m += planned_recovery_cost_m
            # Successful recognition at a deliberately selected stable anchor.
            probability = float(np.clip(0.25 + 0.45 * visual[current] + 0.35 * (1.0 - risk[current]), 0.0, 1.0))
            if rng.random() < probability:
                error *= 0.18
                uncertainty *= 0.18
                in_failure = False
                stabilizations += 1
                last_stabilization = len(trajectory) - 1

        if len(trajectory) % cfg.anchor_stride < len(path) and risk[current] < 0.32:
            if all(abs(current[0] - a[0]) + abs(current[1] - a[1]) > 5 for a in anchors):
                anchors.append(current)

    return SimResult(
        policy=policy,
        seed=seed,
        complete=coverage() >= cfg.coverage_target,
        coverage=coverage(),
        path_m=(len(trajectory) - 1) * world.resolution,
        steps=len(trajectory) - 1,
        pose_rmse_m=float(np.sqrt(np.mean(np.square(errors)))),
        max_pose_error_m=float(max(errors)),
        risk_exposure=risk_exposure * world.resolution,
        failure_steps=failures,
        stabilization_revisits=stabilizations,
        recovery_budget_spent_m=recovery_budget_spent_m,
        decision_count=decisions,
        trajectory=trajectory,
    )
