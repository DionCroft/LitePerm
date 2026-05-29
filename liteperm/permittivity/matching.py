"""Reference comparison and lightweight material-identification helpers."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from liteperm.models.core import MaterialSpectrum


def normalise_material_payload(material: dict[str, Any]) -> dict[str, Any]:
    payload = dict(material)
    payload["material_name"] = payload.get("material_name") or payload.get("display_name") or payload.get("name") or "Unknown Material"
    payload["display_name"] = payload.get("display_name", payload["material_name"])
    payload["epsilon_real"] = float(payload.get("epsilon_real", 1.0))
    payload["epsilon_imag"] = float(payload.get("epsilon_imag", 0.0))
    payload["loss_tangent"] = float(payload.get("loss_tangent", 0.0))
    payload["conductivity_s_per_m"] = float(payload.get("conductivity_s_per_m", 0.0))
    payload["category"] = payload.get("category", "")
    payload["source"] = payload.get("source", "LitePerm reference library")
    payload["notes"] = payload.get("notes", "")
    return payload


def _measured_summary(spectrum: MaterialSpectrum) -> dict[str, float]:
    return {
        "epsilon_real": float(np.mean(spectrum.epsilon_prime)),
        "epsilon_imag": float(np.mean(spectrum.epsilon_double_prime)),
        "loss_tangent": float(np.mean(spectrum.loss_tangent)),
        "conductivity_s_per_m": float(np.mean(spectrum.conductivity_s_per_m)),
    }


def _similarity_score(measured: dict[str, float], reference: dict[str, Any]) -> float:
    metrics = [
        abs(measured["epsilon_real"] - reference["epsilon_real"]) / max(abs(reference["epsilon_real"]), 1.0),
        abs(measured["epsilon_imag"] - reference["epsilon_imag"]) / max(abs(reference["epsilon_imag"]), 0.5),
        abs(measured["loss_tangent"] - reference["loss_tangent"]) / max(abs(reference["loss_tangent"]), 0.05),
        abs(measured["conductivity_s_per_m"] - reference["conductivity_s_per_m"]) / max(abs(reference["conductivity_s_per_m"]), 0.1),
    ]
    error = float(np.mean(metrics))
    return float(max(0.0, 100.0 * np.exp(-1.6 * error)))


def compare_to_reference_materials(spectrum: MaterialSpectrum, materials: list[dict[str, Any]]) -> list[dict[str, Any]]:
    measured = _measured_summary(spectrum)
    rows: list[dict[str, Any]] = []
    for material in materials:
        reference = normalise_material_payload(material)
        similarity = _similarity_score(measured, reference)
        rows.append(
            {
                "material_name": reference["material_name"],
                "display_name": reference["display_name"],
                "category": reference["category"],
                "measured_epsilon_prime": measured["epsilon_real"],
                "reference_epsilon_prime": reference["epsilon_real"],
                "difference_epsilon_prime": measured["epsilon_real"] - reference["epsilon_real"],
                "delta_epsilon_real": measured["epsilon_real"] - reference["epsilon_real"],
                "measured_epsilon_double_prime": measured["epsilon_imag"],
                "reference_epsilon_double_prime": reference["epsilon_imag"],
                "difference_epsilon_double_prime": measured["epsilon_imag"] - reference["epsilon_imag"],
                "delta_epsilon_imag": measured["epsilon_imag"] - reference["epsilon_imag"],
                "measured_loss_tangent": measured["loss_tangent"],
                "reference_loss_tangent": reference["loss_tangent"],
                "measured_conductivity_s_per_m": measured["conductivity_s_per_m"],
                "reference_conductivity_s_per_m": reference["conductivity_s_per_m"],
                "delta_conductivity_s_per_m": measured["conductivity_s_per_m"] - reference["conductivity_s_per_m"],
                "similarity_score": similarity,
                "source": reference["source"],
                "notes": reference["notes"],
            }
        )
    rows.sort(key=lambda row: row["similarity_score"], reverse=True)
    return rows


def identify_closest_materials(spectrum: MaterialSpectrum, materials: list[dict[str, Any]], *, limit: int = 5) -> list[dict[str, Any]]:
    comparisons = compare_to_reference_materials(spectrum, materials)
    matches = []
    for row in comparisons[:limit]:
        matches.append(
            {
                "material_name": row["material_name"],
                "display_name": row.get("display_name", row["material_name"]),
                "category": row["category"],
                "similarity_score": row["similarity_score"],
                "difference_epsilon_prime": row["difference_epsilon_prime"],
                "difference_epsilon_double_prime": row["difference_epsilon_double_prime"],
                "source": row["source"],
            }
        )
    return matches


def comparisons_to_frame(comparisons: list[dict[str, Any]]) -> pd.DataFrame:
    return pd.DataFrame(comparisons)
