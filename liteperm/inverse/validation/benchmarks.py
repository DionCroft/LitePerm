"""Benchmark cases and validation report helpers."""

from __future__ import annotations

from liteperm.inverse.common import ValidationReport


def reference_validation_cases() -> list[dict[str, object]]:
    return [
        {"material": "Water", "epsilon_real": 78.3, "epsilon_imag": 9.5, "sensor_type": "open_ended_coax_probe"},
        {"material": "PTFE", "epsilon_real": 2.1, "epsilon_imag": 0.00042, "sensor_type": "patch_antenna"},
        {"material": "FR4", "epsilon_real": 4.3, "epsilon_imag": 0.086, "sensor_type": "microstrip_resonator"},
        {"material": "Synthetic Saline", "epsilon_real": 76.0, "epsilon_imag": 15.0, "sensor_type": "generic_resonator"},
    ]


def generate_validation_report(cases: list[dict[str, object]] | None = None) -> ValidationReport:
    cases = cases or reference_validation_cases()
    summary = {
        "num_cases": float(len(cases)),
        "mean_reference_epsilon_real": float(sum(case["epsilon_real"] for case in cases) / max(len(cases), 1)),
        "mean_reference_epsilon_imag": float(sum(case["epsilon_imag"] for case in cases) / max(len(cases), 1)),
    }
    return ValidationReport(benchmark_name="LitePerm Phase 3 Reference Benchmarks", cases=cases, summary_metrics=summary)

