"""Model evaluation utilities for VerifAI.

Calculates comprehensive classification metrics suited for imbalanced datasets,
including Precision, Recall, F1-score, PR-AUC, and full confusion matrix counts.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

import numpy as np
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)


def compute_metrics(
    y_true: np.ndarray | list[int],
    y_pred: np.ndarray | list[int],
    y_scores: np.ndarray | list[float] | None = None,
    extra_metadata: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    """Compute detailed evaluation metrics on predictions against ground truth.

    Args:
        y_true: Ground truth binary labels (0 or 1).
        y_pred: Predicted binary labels (0 or 1).
        y_scores: Predicted probabilities or decision scores for positive class (1).
        extra_metadata: Optional dictionary with model name, dataset info, etc.

    Returns:
        Dictionary containing all evaluation metrics and metadata.
    """
    y_true_arr = np.asarray(y_true, dtype=int)
    y_pred_arr = np.asarray(y_pred, dtype=int)

    acc = float(accuracy_score(y_true_arr, y_pred_arr))
    prec = float(precision_score(y_true_arr, y_pred_arr, zero_division=0))
    rec = float(recall_score(y_true_arr, y_pred_arr, zero_division=0))
    f1 = float(f1_score(y_true_arr, y_pred_arr, zero_division=0))

    if y_scores is not None:
        y_scores_arr = np.asarray(y_scores, dtype=float)
        pr_auc = float(average_precision_score(y_true_arr, y_scores_arr))
    else:
        pr_auc = None

    cm = confusion_matrix(y_true_arr, y_pred_arr)
    # cm layout: [[TN, FP], [FN, TP]]
    tn, fp, fn, tp = int(cm[0, 0]), int(cm[0, 1]), int(cm[1, 0]), int(cm[1, 1])

    metrics: Dict[str, Any] = {
        "accuracy": round(acc, 4),
        "precision": round(prec, 4),
        "recall": round(rec, 4),
        "f1_score": round(f1, 4),
        "pr_auc": round(pr_auc, 4) if pr_auc is not None else None,
        "confusion_matrix": {
            "true_negatives": tn,
            "false_positives": fp,
            "false_negatives": fn,
            "true_positives": tp,
        },
        "false_positives": fp,
        "false_negatives": fn,
        "true_positives": tp,
        "true_negatives": tn,
        "total_test_samples": int(len(y_true_arr)),
        "fraudulent_samples": int(np.sum(y_true_arr == 1)),
        "legitimate_samples": int(np.sum(y_true_arr == 0)),
    }

    if extra_metadata:
        metrics.update(extra_metadata)

    return metrics


def save_metrics_to_json(metrics: Dict[str, Any], output_path: str | Path) -> Path:
    """Save metrics dictionary to a formatted JSON file.

    Args:
        metrics: The metrics dictionary to save.
        output_path: File destination path.

    Returns:
        Path object of saved file.
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)
    return path


def load_metrics_from_json(metrics_path: str | Path) -> Dict[str, Any] | None:
    """Load evaluation metrics from JSON file if it exists.

    Args:
        metrics_path: File path to load.

    Returns:
        Dictionary of metrics or None if file not found.
    """
    path = Path(metrics_path)
    if not path.is_file():
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None
