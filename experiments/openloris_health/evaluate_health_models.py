from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, brier_score_loss, roc_auc_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


FEATURE_SETS = {
    "covariance": ["cov_trace_xyyaw"],
    "visual": ["visual_inlier_ratio", "features", "matches", "inliers"],
    "lidar": [
        "icp_inliers_ratio",
        "icp_structural_complexity",
        "icp_correspondences",
        "scan_valid_ratio",
        "scan_range_std_m",
    ],
    "cross_modal": [
        "visual_inlier_ratio",
        "features",
        "matches",
        "inliers",
        "icp_inliers_ratio",
        "icp_structural_complexity",
        "icp_correspondences",
        "scan_valid_ratio",
        "scan_range_std_m",
        "cov_trace_xyyaw",
    ],
}


def expand_window_feature_sets(frame: pd.DataFrame) -> dict[str, list[str]]:
    feature_sets = {name: columns.copy() for name, columns in FEATURE_SETS.items()}
    window_columns = [column for column in frame.columns if "__" in column]
    if not window_columns:
        return feature_sets
    visual_prefixes = ("visual_inlier_ratio__", "features__")
    lidar_prefixes = (
        "icp_inliers_ratio__",
        "icp_structural_complexity__",
        "icp_correspondences__",
        "scan_valid_ratio__",
    )
    covariance_columns = [column for column in window_columns if column.startswith("cov_log1p__")]
    visual_columns = [column for column in window_columns if column.startswith(visual_prefixes)]
    lidar_columns = [column for column in window_columns if column.startswith(lidar_prefixes)]
    feature_sets["covariance_window"] = ["cov_log1p", *covariance_columns]
    feature_sets["visual_window"] = [*feature_sets["visual"], *visual_columns]
    feature_sets["lidar_window"] = [*feature_sets["lidar"], *lidar_columns]
    feature_sets["cross_modal_window"] = [
        *feature_sets["cross_modal"], "cov_log1p", *visual_columns, *lidar_columns, *covariance_columns
    ]
    return feature_sets


def expected_calibration_error(y: np.ndarray, probability: np.ndarray, bins: int = 10) -> float:
    edges = np.linspace(0.0, 1.0, bins + 1)
    total = len(y)
    value = 0.0
    for low, high in zip(edges[:-1], edges[1:]):
        include = (probability >= low) & (probability < high if high < 1.0 else probability <= high)
        if np.any(include):
            value += np.count_nonzero(include) / total * abs(float(y[include].mean()) - float(probability[include].mean()))
    return value


def build_model(columns: list[str]) -> Pipeline:
    numeric = Pipeline([("impute", SimpleImputer(strategy="median")), ("scale", StandardScaler())])
    return Pipeline(
        [
            ("features", ColumnTransformer([("numeric", numeric, columns)], remainder="drop")),
            ("model", LogisticRegression(class_weight="balanced", max_iter=2000, random_state=20260813)),
        ]
    )


def score(y: np.ndarray, probability: np.ndarray) -> dict[str, float]:
    if len(np.unique(y)) < 2:
        raise ValueError("test labels contain only one class")
    return {
        "auroc": roc_auc_score(y, probability),
        "auprc": average_precision_score(y, probability),
        "brier": brier_score_loss(y, probability),
        "ece_10": expected_calibration_error(y, probability),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Chronological/cross-scene health-model gate.")
    parser.add_argument("--train", type=Path, required=True)
    parser.add_argument("--test", type=Path, help="Held-out scene CSV. Omit only for a smoke split.")
    parser.add_argument("--train-fraction", type=float, default=0.60)
    parser.add_argument("--gap-s", type=float, default=1.0)
    parser.add_argument("--label", default="future_rpe_event")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    raw_train = pd.read_csv(args.train)
    eligibility = "eligible_prediction" if "eligible_prediction" in raw_train else "has_future_label"
    train_frame = raw_train.query(f"{eligibility} == 1").sort_values("stamp")
    if args.test:
        raw_test = pd.read_csv(args.test)
        test_eligibility = "eligible_prediction" if "eligible_prediction" in raw_test else "has_future_label"
        test_frame = raw_test.query(f"{test_eligibility} == 1").sort_values("stamp")
        split_note = "cross-scene"
    else:
        cut = int(len(train_frame) * args.train_fraction)
        split_stamp = float(train_frame.iloc[cut].stamp)
        test_frame = train_frame[train_frame.stamp >= split_stamp + args.gap_s].copy()
        train_frame = train_frame.iloc[:cut].copy()
        split_note = f"chronological smoke split with {args.gap_s:.1f}s embargo"

    rows = []
    y_train = train_frame[args.label].to_numpy(dtype=int)
    y_test = test_frame[args.label].to_numpy(dtype=int)
    prevalence_probability = np.full(len(test_frame), float(y_train.mean()))
    rows.append({"model": "prevalence", **score(y_test, prevalence_probability)})

    for name, columns in expand_window_feature_sets(train_frame).items():
        model = build_model(columns)
        model.fit(train_frame, y_train)
        rows.append({"model": name, **score(y_test, model.predict_proba(test_frame)[:, 1])})

    table = pd.DataFrame(rows)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    table.to_csv(args.output.with_suffix(".csv"), index=False)
    lines = [
        "# Health model gate",
        "",
        f"Split: {split_note}. Label: `{args.label}`.",
        "",
        f"Train rows/positive rate: {len(train_frame)} / {y_train.mean():.3f}",
        f"Test rows/positive rate: {len(test_frame)} / {y_test.mean():.3f}",
        "",
        "```text",
        table.round(4).to_string(index=False),
        "```",
        "",
        "A chronological same-sequence result is a leakage-resistant smoke test, not cross-scene evidence.",
    ]
    args.output.write_text("\n".join(lines), encoding="utf-8")
    print(table.round(4).to_string(index=False))


if __name__ == "__main__":
    main()
