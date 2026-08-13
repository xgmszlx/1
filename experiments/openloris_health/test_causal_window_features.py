import numpy as np
import pandas as pd

from build_causal_window_features import add_causal_features


def test_future_changes_do_not_alter_past_features():
    frame = pd.DataFrame(
        {
            "stamp": np.arange(10, dtype=float) * 0.1,
            "visual_inlier_ratio": np.linspace(0.1, 0.9, 10),
            "features": np.arange(10) + 10,
            "icp_inliers_ratio": np.linspace(0.9, 0.1, 10),
            "icp_structural_complexity": np.linspace(0.2, 0.4, 10),
            "icp_correspondences": np.arange(10) + 100,
            "scan_valid_ratio": np.ones(10),
            "cov_trace_xyyaw": np.linspace(0.01, 0.1, 10),
        }
    )
    changed = frame.copy()
    changed.loc[7:, "visual_inlier_ratio"] = 99.0
    original_features = add_causal_features(frame, (0.5,))
    changed_features = add_causal_features(changed, (0.5,))
    generated = [column for column in original_features if "__" in column]
    pd.testing.assert_frame_equal(
        original_features.loc[:6, generated], changed_features.loc[:6, generated]
    )
