"""Built-in Komarov transformation plugin."""

from __future__ import annotations

import numpy as np

from liteperm.plugins.base import TransformationContext, TransformationPlugin
from liteperm.plugins.builtin.helpers import admittance_to_epsilon, build_spectrum


class KomarovPlugin(TransformationPlugin):
    def name(self) -> str:
        return "komarov"

    def description(self) -> str:
        return "Dispersive correction layer applied to a geometry-normalised admittance inversion."

    def calculate(self, context: TransformationContext):
        epsilon_complex = admittance_to_epsilon(context.measurement.frequency_hz, context.admittance, context.geometry)
        outer_radius_mm = float(context.geometry.parameters.get("outer_radius_mm", 2.05))
        dispersive_term = 1.0 + 1j * 0.01 * (outer_radius_mm / 2.05) * (context.measurement.frequency_hz / np.max(context.measurement.frequency_hz))
        epsilon_complex = epsilon_complex / dispersive_term
        return build_spectrum(
            frequency_hz=context.measurement.frequency_hz,
            gamma=context.gamma,
            impedance=context.impedance,
            admittance=context.admittance,
            epsilon_complex=epsilon_complex,
            method_name="Komarov",
            metadata=self.metadata(),
        )

    def validate(self, context: TransformationContext) -> list[str]:
        issues: list[str] = []
        if context.geometry.sensor_type != "open_ended_coax_probe":
            issues.append("Komarov support is currently oriented to coaxial-probe style geometries.")
        return issues

    def metadata(self) -> dict[str, object]:
        return {
            "display_name": "Komarov",
            "validation_status": "experimental",
            "assumptions": "Architecture placeholder for dispersive full-wave probe models.",
            "implemented": True,
            "family": "OECP",
        }

