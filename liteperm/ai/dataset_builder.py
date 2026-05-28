"""Dataset assembly helpers for experiment archives."""

from __future__ import annotations

import pandas as pd

from liteperm.ai.feature_extraction import extract_spectrum_features
from liteperm.models.core import ExperimentRecord


def build_experiment_dataset(records: list[ExperimentRecord]) -> pd.DataFrame:
    rows = []
    for record in records:
        features = extract_spectrum_features(record.processed_measurement, record.spectrum)
        features.update(
            {
                "experiment_id": record.experiment_id,
                "experiment_name": record.metadata.experiment_name,
                "project_name": record.metadata.project_name,
                "researcher": record.metadata.researcher,
                "sensor_type": record.metadata.sensor_type,
                "material_under_test": record.metadata.material_under_test,
                "tags": ",".join(record.metadata.tags),
            }
        )
        rows.append(features)
    return pd.DataFrame(rows)

