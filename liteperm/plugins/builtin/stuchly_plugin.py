"""Built-in Stuchly transformation plugin."""

from __future__ import annotations

from liteperm.plugins.base import TransformationContext, TransformationPlugin
from liteperm.plugins.builtin.helpers import admittance_to_epsilon, build_spectrum


class StuchlyPlugin(TransformationPlugin):
    def name(self) -> str:
        return "stuchly"

    def description(self) -> str:
        return "Admittance-based quasi-static OECP inversion with a geometry-derived cell constant."

    def calculate(self, context: TransformationContext):
        epsilon_complex = admittance_to_epsilon(context.measurement.frequency_hz, context.admittance, context.geometry)
        return build_spectrum(
            frequency_hz=context.measurement.frequency_hz,
            gamma=context.gamma,
            impedance=context.impedance,
            admittance=context.admittance,
            epsilon_complex=epsilon_complex,
            method_name="Stuchly",
            metadata=self.metadata(),
        )

    def validate(self, context: TransformationContext) -> list[str]:
        issues: list[str] = []
        if context.geometry.sensor_type not in {"open_ended_coax_probe", "patch_antenna", "generic_resonator"}:
            issues.append("Stuchly is best suited to probes, capacitive sensors, or first-pass resonator studies.")
        return issues

    def metadata(self) -> dict[str, object]:
        return {
            "display_name": "Stuchly",
            "validation_status": "baseline",
            "assumptions": "First-pass quasi-static reconstruction for reflection-based dielectric sensing.",
            "implemented": True,
            "family": "OECP / capacitive",
        }

