"""Parameter sweep engine for inverse and forward studies."""

from __future__ import annotations

import itertools

import numpy as np
import pandas as pd

from liteperm.inverse.common import ParameterSweepResult, clone_with_parameter_updates
from liteperm.inverse.optimisers.error_metrics import compute_scalar_error


class ParameterSweepEngine:
    def run(
        self,
        *,
        model,
        measured_measurement,
        parameter_grid: dict[str, list[float]],
        error_metric: str = "weighted_error",
    ) -> ParameterSweepResult:
        rows = []
        for values in itertools.product(*parameter_grid.values()):
            updates = dict(zip(parameter_grid.keys(), values, strict=True))
            candidate_model = clone_with_parameter_updates(model, updates)
            simulation = candidate_model.simulate(measured_measurement.frequency_hz)
            predicted = simulation.measurement
            rows.append(
                {
                    **updates,
                    "objective": compute_scalar_error(measured_measurement, predicted, metric=error_metric),
                    "predicted_resonant_frequency_hz": simulation.predicted_resonant_frequency_hz,
                    "effective_epsilon_real": float(np.mean(simulation.effective_permittivity_complex.real)),
                }
            )
        return ParameterSweepResult(sweep_table=pd.DataFrame(rows), metadata={"error_metric": error_metric})

