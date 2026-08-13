# Search and Screening Protocol

## Research scope

Single-robot active SLAM and adjacent work needed to build a practical closed
loop: active mapping/exploration, localization-aware planning, active loop
closure, perception-aware navigation, failure-aware view planning, and
uncertainty-aware goal/path selection.

## Source priority

1. Publisher or author-hosted full paper and supplement.
2. Official project page and repository linked by the authors.
3. DOI/Crossref/arXiv/OpenReview metadata.
4. Curated paper lists only for discovery, never as final evidence.

## Venue emphasis

- Journals: IEEE T-RO, IJRR, Science Robotics, IEEE RA-L, RAS, and relevant
  IEEE Transactions journals.
- Conferences: RSS, ICRA, IROS, CoRL, CVPR/ICCV/ECCV when the contribution is
  directly relevant to active visual localization or mapping.
- Lower-tier papers may supply reusable modules, but cannot establish the main
  research gap by themselves.

## Time window

- Core contemporary corpus: 2018-2026.
- Earlier foundational work is included when later papers depend on it.

## Inclusion criteria

- Plans actions/views/paths using map, pose, perception, or SLAM uncertainty.
- Reports localization and/or mapping quality, not coverage alone.
- Has enough method detail to identify reusable modules.
- For implementation shortlist: official code plus accessible data/simulator.

## Exclusion or down-ranking criteria

- Pure frontier exploration presented as active SLAM without SLAM-quality
  objectives or measurements.
- No official code and no independently reproducible algorithmic specification.
- Requires multi-GPU training, proprietary data, or specialized 3D LiDAR/UAV
  hardware for the core contribution.
- Only self-collected data with unavailable ground truth.
- Evaluation lacks strong baselines, repeated trials, or uncertainty reporting.

## Decision columns

Each retained work is recorded by problem, sensing, SLAM backend, planning
representation, utility/objective, data/simulator, official code, ROS version,
hardware burden, reported metrics, reusable module, known limitation, evidence
label, and source URL.

## Search log and stopping rule

Searches run on 2026-08-13 used publisher pages, arXiv, DOI/Crossref metadata,
official project pages, and GitHub repositories. Query clusters included:

- `active SLAM survey`, `SLAM-aware exploration`, `pose graph active SLAM`;
- `perception-aware exploration` plus `visual features`, `LiDAR degeneracy`,
  `Fisher information`, and `feature-limited`;
- `active loop closure`, `global graph stabilization`, and `loop-aware exploration`;
- exact-match combinations of `sensor health`, `cross-modal`, `camera/RGB-D`,
  `2D LiDAR`, `active SLAM`, `active exploration`, `ground robot`, and `ROS2`;
- official-code searches for each shortlisted title and implementation concept.

Backward references from the 2023 T-RO survey and forward/recent-title searches
through August 2026 were used to reduce recency bias. The search is considered
adequate for a *provisional* topic only when each module has a strong prior-art
boundary and repeated exact-match searches stop producing a closer paper. It is
not considered exhaustive until Scopus/Web of Science/IEEE Xplore queries are
exported through the user's institutional access and independently screened.

Negative search results are recorded only as “not found in the inspected
corpus”; they are never converted into an absolute novelty claim.
