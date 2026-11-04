"""Machine Learning training pipeline for VerifAI.

Trains and compares TF-IDF + Logistic Regression and TF-IDF + Calibrated Linear SVM
on the Employment Scam Aegean Dataset (EMSCAD). Evaluates on a stratified held-out
test set and exports the best model and performance metrics.
"""

from __future__ import annotations

import argparse
import logging
from pathlib import Path
import sys

import joblib
import numpy as np
import pandas as pd
from sklearn.calibration import CalibratedClassifierCV
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, f1_score
from sklearn.model_selection import StratifiedKFold, cross_validate, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.svm import LinearSVC

# Support direct script execution and package imports
CURRENT_DIR = Path(__file__).resolve().parent
if str(CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(CURRENT_DIR))

from evaluate import compute_metrics, save_metrics_to_json  # noqa: E402
from preprocess import combine_text_fields  # noqa: E402

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("VerifAI.ML.Train")

DEFAULT_DATA_PATH = CURRENT_DIR / "data" / "fake_job_postings.csv"
DEFAULT_MODEL_DIR = CURRENT_DIR / "saved_model"
RANDOM_STATE = 42


def load_and_prepare_dataset(data_path: Path) -> tuple[pd.Series, pd.Series]:
    """Load dataset, handle missing values, remove duplicates, and prepare text & labels.

    Args:
        data_path: Path to fake_job_postings.csv.

    Returns:
        Tuple of (clean_text_series, target_labels).
    """
    if not data_path.is_file():
        raise FileNotFoundError(
            f"Dataset not found at '{data_path}'. Please place 'fake_job_postings.csv' "
            f"in '{data_path.parent}'."
        )

    logger.info("Loading dataset from %s", data_path)
    df = pd.read_csv(data_path)
    logger.info("Raw dataset shape: %s", df.shape)

    # Validate target column
    if "fraudulent" not in df.columns:
        raise ValueError("Missing required target column 'fraudulent' in dataset.")

    # Drop duplicate records based on core text content if any
    initial_count = len(df)
    subset_cols = [c for c in ["title", "company_profile", "description"] if c in df.columns]
    df = df.drop_duplicates(subset=subset_cols).copy()
    logger.info("Removed %d duplicate rows. Remaining: %d", initial_count - len(df), len(df))

    # Combine text features
    logger.info("Combining text fields and preprocessing text...")
    X_text = combine_text_fields(df)
    y = df["fraudulent"].astype(int)

    # Class balance inspection
    class_counts = y.value_counts().to_dict()
    logger.info(
        "Class distribution: Legitimate (0): %d, Fraudulent (1): %d (%.2f%%)",
        class_counts.get(0, 0),
        class_counts.get(1, 0),
        (class_counts.get(1, 0) / len(y)) * 100 if len(y) > 0 else 0,
    )

    return X_text, y


def build_tfidf_vectorizer() -> TfidfVectorizer:
    """Construct TF-IDF Vectorizer matching the architectural specification."""
    return TfidfVectorizer(
        max_features=30000,
        ngram_range=(1, 2),
        min_df=2,
        sublinear_tf=True,
        strip_accents="unicode",
    )


def train_and_compare_models(
    X_train: pd.Series,
    y_train: pd.Series,
) -> tuple[str, Pipeline]:
    """Train candidate models via cross-validation and select the best based on PR-AUC & F1.

    Args:
        X_train: Training text series.
        y_train: Training labels.

    Returns:
        Tuple of (winner_name, trained_winner_pipeline).
    """
    logger.info("Setting up candidate pipelines...")

    # Candidate 1: TF-IDF + Logistic Regression (Balanced)
    lr_pipeline = Pipeline([
        ("tfidf", build_tfidf_vectorizer()),
        (
            "clf",
            LogisticRegression(
                class_weight="balanced",
                max_iter=1000,
                random_state=RANDOM_STATE,
                C=1.0,
            ),
        ),
    ])

    # Candidate 2: TF-IDF + Calibrated Linear SVM (Balanced)
    # CalibratedClassifierCV ensures standard calibrated predict_proba support
    svm_base = LinearSVC(
        class_weight="balanced",
        random_state=RANDOM_STATE,
        max_iter=2000,
    )
    svm_pipeline = Pipeline([
        ("tfidf", build_tfidf_vectorizer()),
        ("clf", CalibratedClassifierCV(estimator=svm_base, cv=3)),
    ])

    candidates = {
        "LogisticRegression": lr_pipeline,
        "CalibratedLinearSVM": svm_pipeline,
    }

    cv = StratifiedKFold(n_splits=3, shuffle=True, random_state=RANDOM_STATE)
    cv_results = {}

    for name, pipeline in candidates.items():
        logger.info("Evaluating %s via 3-fold cross-validation...", name)
        scores = cross_validate(
            pipeline,
            X_train,
            y_train,
            cv=cv,
            scoring=["f1", "precision", "recall"],
            n_jobs=1,  # Windows-friendly synchronous execution
            return_train_score=False,
        )
        mean_f1 = float(np.mean(scores["test_f1"]))
        mean_prec = float(np.mean(scores["test_precision"]))
        mean_rec = float(np.mean(scores["test_recall"]))
        logger.info(
            "%s CV Results -> F1: %.4f, Precision: %.4f, Recall: %.4f",
            name,
            mean_f1,
            mean_prec,
            mean_rec,
        )
        cv_results[name] = {"f1": mean_f1, "pipeline": pipeline}

    # Select best model based on cross-validation F1-score
    winner_name = max(cv_results, key=lambda k: cv_results[k]["f1"])
    winner_pipeline = cv_results[winner_name]["pipeline"]
    logger.info("Selected winning model: %s (CV F1: %.4f)", winner_name, cv_results[winner_name]["f1"])

    # Fit selected pipeline on all training data
    logger.info("Fitting winning pipeline '%s' on full training set...", winner_name)
    winner_pipeline.fit(X_train, y_train)

    return winner_name, winner_pipeline


def run_training_pipeline(
    data_path: Path = DEFAULT_DATA_PATH,
    output_dir: Path = DEFAULT_MODEL_DIR,
) -> dict:
    """Execute end-to-end training, model selection, evaluation, and serialization.

    Args:
        data_path: Path to dataset CSV.
        output_dir: Directory to save serialized model and metrics.

    Returns:
        Evaluation metrics dictionary.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    model_output_file = output_dir / "model.joblib"
    metrics_output_file = output_dir / "metrics.json"

    # Step 1: Load and clean data
    X_text, y = load_and_prepare_dataset(data_path)

    # Step 2: Stratified Train/Test Split (80% train, 20% test)
    logger.info("Splitting dataset (80%% train, 20%% test, stratified)...")
    X_train, X_test, y_train, y_test = train_test_split(
        X_text,
        y,
        test_size=0.20,
        random_state=RANDOM_STATE,
        stratify=y,
    )
    logger.info("Train set: %d samples, Test set: %d samples", len(X_train), len(X_test))

    # Step 3: Model comparison and training
    winner_name, winning_pipeline = train_and_compare_models(X_train, y_train)

    # Step 4: Evaluate winning model on held-out test set
    logger.info("Evaluating selected model '%s' on held-out test set...", winner_name)
    y_pred = winning_pipeline.predict(X_test)

    # Obtain positive class probabilities
    if hasattr(winning_pipeline, "predict_proba"):
        y_scores = winning_pipeline.predict_proba(X_test)[:, 1]
    elif hasattr(winning_pipeline, "decision_function"):
        y_scores = winning_pipeline.decision_function(X_test)
    else:
        y_scores = None

    metadata = {
        "model_name": f"TF-IDF + {winner_name} (Balanced)",
        "dataset_name": "Employment Scam Aegean Dataset (EMSCAD)",
        "selected_model_type": winner_name,
        "random_state": RANDOM_STATE,
        "test_split_ratio": 0.20,
    }

    metrics = compute_metrics(
        y_true=y_test,
        y_pred=y_pred,
        y_scores=y_scores,
        extra_metadata=metadata,
    )

    logger.info("Test set results:")
    logger.info("  Accuracy:  %.4f", metrics["accuracy"])
    logger.info("  Precision: %.4f", metrics["precision"])
    logger.info("  Recall:    %.4f", metrics["recall"])
    logger.info("  F1-Score:  %.4f", metrics["f1_score"])
    if metrics["pr_auc"] is not None:
        logger.info("  PR-AUC:    %.4f", metrics["pr_auc"])
    logger.info("  Confusion Matrix: %s", metrics["confusion_matrix"])

    # Step 5: Save model and metrics
    logger.info("Saving trained pipeline to %s", model_output_file)
    joblib.dump(winning_pipeline, model_output_file, compress=3)

    logger.info("Saving metrics to %s", metrics_output_file)
    save_metrics_to_json(metrics, metrics_output_file)

    logger.info("Training pipeline completed successfully.")
    return metrics


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="VerifAI ML Training Pipeline")
    parser.add_argument(
        "--data",
        type=Path,
        default=DEFAULT_DATA_PATH,
        help="Path to fake_job_postings.csv",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_MODEL_DIR,
        help="Directory to save model and metrics",
    )
    args = parser.parse_args()

    run_training_pipeline(data_path=args.data, output_dir=args.output_dir)
