import numpy as np
import pandas as pd

from label_health_csv import label_dataframe, rigid_alignment_2d, wrap_angle


def test_rigid_alignment_recovers_transform():
    source = np.array([[0.0, 0.0], [1.0, 0.0], [0.0, 2.0], [1.5, 1.0]])
    angle = 0.4
    rotation = np.array([[np.cos(angle), -np.sin(angle)], [np.sin(angle), np.cos(angle)]])
    translation = np.array([3.0, -2.0])
    target = (rotation @ source.T).T + translation
    estimated_rotation, estimated_translation = rigid_alignment_2d(source, target)
    assert np.allclose(estimated_rotation, rotation)
    assert np.allclose(estimated_translation, translation)


def test_label_dataframe_has_near_zero_error_for_rigidly_transformed_track():
    stamps = np.arange(100.0, 103.0, 0.1)
    odom_x = stamps - 100.0
    odom_y = 0.2 * (stamps - 100.0)
    health = pd.DataFrame(
        {
            "stamp": stamps,
            "odom_x_m": odom_x,
            "odom_y_m": odom_y,
            "odom_yaw_rad": np.full(len(stamps), 0.2),
            "lost": np.zeros(len(stamps), dtype=int),
        }
    )
    angle = 0.3
    co, si = np.cos(angle), np.sin(angle)
    gt_x = co * odom_x - si * odom_y + 5.0
    gt_y = si * odom_x + co * odom_y - 1.0
    gt_yaw = np.full(len(stamps), angle + 0.2)
    gt = np.column_stack(
        (
            stamps,
            gt_x,
            gt_y,
            np.zeros(len(stamps)),
            np.zeros(len(stamps)),
            np.zeros(len(stamps)),
            np.sin(gt_yaw / 2.0),
            np.cos(gt_yaw / 2.0),
        )
    )
    labeled = label_dataframe(health, gt, 0.5, 1.0, 0.3)
    assert labeled.position_error_m.max() < 1e-10
    assert np.abs(wrap_angle(labeled.aligned_odom_yaw_rad - labeled.gt_yaw_rad)).max() < 1e-10
    assert labeled.future_failure.sum() == 0
    assert labeled.future_error_growth_event.sum() == 0
    assert labeled.future_new_lost.sum() == 0
    assert labeled.future_rpe_event.sum() == 0
    assert labeled.eligible_prediction.sum() < len(labeled)


def test_current_lost_row_is_not_eligible_for_prediction():
    stamps = np.arange(100.0, 102.0, 0.1)
    health = pd.DataFrame(
        {
            "stamp": stamps,
            "odom_x_m": stamps - 100.0,
            "odom_y_m": np.zeros(len(stamps)),
            "odom_yaw_rad": np.zeros(len(stamps)),
            "lost": np.r_[1, np.zeros(len(stamps) - 1, dtype=int)],
        }
    )
    gt = np.column_stack(
        (
            stamps,
            stamps - 100.0,
            np.zeros((len(stamps), 5)),
            np.ones(len(stamps)),
        )
    )
    labeled = label_dataframe(health, gt, 0.5, 1.0, 0.3)
    assert labeled.eligible_prediction.iloc[0] == 0
