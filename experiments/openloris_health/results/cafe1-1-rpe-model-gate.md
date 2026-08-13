# Health model gate

Split: chronological smoke split with 1.0s embargo. Label: `future_rpe_event`.

Train rows/positive rate: 600 / 0.327
Test rows/positive rate: 382 / 0.723

```text
             model  auroc  auprc  brier  ece_10
        prevalence 0.5000 0.7225 0.3572  0.3958
        covariance 0.4406 0.6660 0.2497  0.2219
            visual 0.6380 0.8293 0.2098  0.1038
             lidar 0.3908 0.7272 0.3000  0.2876
       cross_modal 0.6125 0.8299 0.2812  0.2260
 covariance_window 0.6702 0.8470 0.2374  0.1931
     visual_window 0.6378 0.8118 0.2848  0.2920
      lidar_window 0.2836 0.6091 0.3544  0.3735
cross_modal_window 0.4612 0.6884 0.4778  0.4775
```

A chronological same-sequence result is a leakage-resistant smoke test, not cross-scene evidence.