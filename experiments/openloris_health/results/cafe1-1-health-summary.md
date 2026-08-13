# OpenLORIS cafe1-1 health smoke summary

This verifies that both visual and 2-D LiDAR/ICP online signals are emitted and non-constant. It is not a predictive-model result.

- Rows: 1127
- Duration represented: 56.848 s
- Backend lost rows: 127

```text
                            count       mean        std        min         5%        50%        95%          max
visual_inlier_ratio        1127.0    0.71245    0.26527    0.00000    0.00000    0.80922    0.91268      0.98857
features                   1127.0  904.06389   33.53847  694.00000  851.00000  907.00000  953.70000    974.00000
icp_inliers_ratio          1127.0    0.54297    0.27923    0.00000    0.00000    0.66528    0.83889      0.89861
icp_structural_complexity  1127.0    0.27973    0.10213    0.00000    0.00000    0.30890    0.36311      0.38196
icp_correspondences        1127.0  390.93966  201.04820    0.00000    0.00000  479.00000  604.00000    647.00000
cov_trace_xyyaw            1127.0   26.93889  893.53471    0.00019    0.00051    0.00370    3.00000  29997.00000
scan_valid_ratio           1127.0    0.96773    0.02493    0.86389    0.91389    0.97222    0.99583      1.00000
estimation_time_s          1127.0    0.04171    0.01080    0.00972    0.02994    0.03899    0.05719      0.10566
```
