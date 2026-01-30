"""
Drift Detection

Detects data and model drift.
"""

import logging
from typing import Any, Dict, Optional

import numpy as np

logger = logging.getLogger(__name__)


class DriftDetector:
    """
    Detects data and model drift.

    Provides statistical tests for data drift, model drift detection,
    and concept drift detection with alerting.
    """

    def __init__(self, tenant_id: Optional[str] = None):
        """
        Initialize drift detector.

        Args:
            tenant_id: Optional tenant ID
        """
        self.tenant_id = tenant_id

        logger.info(f"DriftDetector initialized for tenant: {tenant_id}")

    def detect_data_drift(
        self, reference_data: np.ndarray, current_data: np.ndarray, threshold: float = 0.05
    ) -> Dict[str, Any]:
        """
        Detect data drift using statistical tests.

        Args:
            reference_data: Reference dataset
            current_data: Current dataset
            threshold: P-value threshold for drift

        Returns:
            Drift detection results
        """
        try:
            from scipy import stats

            # Kolmogorov-Smirnov test
            result = stats.ks_2samp(reference_data.flatten(), current_data.flatten())

            drift_detected = result.pvalue < threshold  # type: ignore[attr-defined]

            return {
                "drift_detected": drift_detected,
                "p_value": float(result.pvalue),  # type: ignore[attr-defined]
                "statistic": float(result.statistic),  # type: ignore[attr-defined]
                "threshold": threshold,
            }
        except Exception as e:
            logger.error(f"Data drift detection failed: {str(e)}")
            return {"drift_detected": False, "error": str(e)}

    def detect_model_drift(
        self,
        reference_metrics: Dict[str, float],
        current_metrics: Dict[str, float],
        threshold: float = 0.1,
    ) -> Dict[str, Any]:
        """
        Detect model drift based on performance degradation.

        Args:
            reference_metrics: Reference performance metrics
            current_metrics: Current performance metrics
            threshold: Performance degradation threshold

        Returns:
            Model drift detection results
        """
        drift_detected = False
        degradation = {}

        for metric_name in reference_metrics:
            if metric_name in current_metrics:
                ref_value = reference_metrics[metric_name]
                curr_value = current_metrics[metric_name]

                # Calculate relative degradation
                if ref_value != 0:
                    rel_degradation = abs(curr_value - ref_value) / abs(ref_value)
                    degradation[metric_name] = rel_degradation

                    if rel_degradation > threshold:
                        drift_detected = True

        return {
            "drift_detected": drift_detected,
            "degradation": degradation,
            "threshold": threshold,
        }

    def check_drift(
        self,
        reference_data: Optional[np.ndarray] = None,
        current_data: Optional[np.ndarray] = None,
        reference_metrics: Optional[Dict[str, float]] = None,
        current_metrics: Optional[Dict[str, float]] = None,
    ) -> Dict[str, Any]:
        """
        Check for drift (data or model).

        Args:
            reference_data: Optional reference data
            current_data: Optional current data
            reference_metrics: Optional reference metrics
            current_metrics: Optional current metrics

        Returns:
            Drift check results
        """
        results = {}

        if reference_data is not None and current_data is not None:
            results["data_drift"] = self.detect_data_drift(reference_data, current_data)

        if reference_metrics is not None and current_metrics is not None:
            results["model_drift"] = self.detect_model_drift(reference_metrics, current_metrics)

        return results
