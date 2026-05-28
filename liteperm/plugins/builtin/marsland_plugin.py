"""Built-in Marsland transformation plugin."""

from __future__ import annotations

import numpy as np

from liteperm.plugins.base import TransformationContext, TransformationPlugin
from liteperm.plugins.builtin.helpers import admittance_to_epsilon, build_spectrum


class MarslandPlugin(TransformationPlugin):
    def name(self) -> str:
        return "marsland"

    def description(self) -> str:
        return "Stuchly-style inversion with a lightweight fringing correction for broadband probe studies."

    def calculate(self, context: TransformationContext):
        epsilon_complex = admittance_to_epsilon(context.measurement.frequency_hz, context.admittance, context.geometry)
        flange_radius_mm = float(context.geometry.parameters.get("flange_radius_mm", 6.0))
        correction = 1.0 + 0.015 * np.sqrt(context.measurement.frequency_hz / np.max(context.measurement.frequency_hz)) + 0.0025 * flange_radius_mm
        epsilon_complex = epsilon_complex / correction
        return build_spectrum(
            frequency_hz=context.measurement.frequency_hz,
            gamma=context.gamma,
            impedance=context.impedance,
            admittance=context.admittance,
            epsilon_complex=epsilon_complex,
            method_name="Marsland",
            metadata=self.metadata(),
        )

    def validate(self, context: TransformationContext) -> list[str]:
        issues: list[str] = []
        if context.geometry.sensor_type != "open_ended_coax_probe":
            issues.append("Marsland corrections are primarily intended for flange-backed OECP workflows.")
        return issues

    def metadata(self) -> dict[str, object]:
        return {
            "display_name": "Marsland",
            "validation_status": "experimental",
            "assumptions": "Approximate fringing correction layer for broadband open-ended coax probes.",
            "implemented": True,
            "family": "OECP",
        }

