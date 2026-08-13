# Recovery-detour-budget sensitivity

5 seeded synthetic trials per cell. The budget is a conservative twice-anchor-distance estimate. This is a mechanism sensitivity test, not SLAM evidence.

```text
                             path_m  pose_rmse_m  failure_steps  stabilization_revisits  recovery_budget_spent_m
scenario           budget_m
common_mode        0.0        49.00       0.5429            2.4                     0.0                      0.0
                   4.0        49.00       0.5429            2.4                     0.0                      0.0
                   8.0        49.00       0.5429            2.4                     0.0                      0.0
                   12.0       49.00       0.5429            2.4                     0.0                      0.0
                   16.0       61.50       0.3739            2.2                     1.0                     12.5
complementary      0.0        49.00       0.5017            4.2                     0.0                      0.0
                   4.0        49.00       0.5017            4.2                     0.0                      0.0
                   8.0        49.00       0.5017            4.2                     0.0                      0.0
                   12.0       49.00       0.5017            4.2                     0.0                      0.0
                   16.0       55.25       0.3033            1.0                     1.0                     12.5
visual_degradation 0.0        56.50       0.2321            0.0                     0.0                      0.0
                   4.0        56.50       0.2321            0.0                     0.0                      0.0
                   8.0        56.50       0.2321            0.0                     0.0                      0.0
                   12.0       56.50       0.2321            0.0                     0.0                      0.0
                   16.0       56.50       0.2321            0.0                     0.0                      0.0
```
