"""Simplified open-ended coaxial probe forward model."""

from __future__ import annotations

import numpy as np

from liteperm.inverse.common import ForwardSimulation, ParameterDefinition
from liteperm.inverse.forward_models.base import ForwardModel, angular_frequency, coax_probe_capacitance
from liteperm.transform.network import impedance_to_gamma


class OpenEndedCoaxProbeModel(ForwardModel):
    def simulate(self, frequency_hz: np.ndarray) -> ForwardSimulation:
        params = self.geometry.parameters
        inner_radius_m = float(params.get("inner_radius_mm", 0.6)) * 1e-3
        outer_radius_m = float(params.get("outer_radius_mm", 2.05)) * 1e-3
        flange_radius_m = float(params.get("flange_radius_mm", 6.0)) * 1e-3
        effective_length_m = max(flange_radius_m, outer_radius_m)
        epsilon_complex = self.layer_stack.effective_epsilon(decay_length_m=max(self.layer_stack.total_thickness_m(), 1e-4))
        conductivity = sum(layer.conductivity_s_per_m for layer in self.layer_stack.layers)
        c0 = coax_probe_capacitance(inner_radius_m, outer_radius_m, effective_length_m)
        omega = angular_frequency(frequency_hz)
        admittance = 1j * omega * c0 * epsilon_complex + conductivity * c0
        impedance = 1 / np.where(np.abs(admittance) < 1e-12, 1e-12, admittance)
        gamma = impedance_to_gamma(impedance, z0=self.z0)
        return ForwardSimulation(
            frequency_hz=np.asarray(frequency_hz, dtype=float),
            s11=gamma,
            impedance=impedance,
            admittance=admittance,
            predicted_resonant_frequency_hz=float(frequency_hz[np.argmin(np.abs(gamma))]),
            effective_permittivity_complex=np.full_like(np.asarray(frequency_hz, dtype=float), epsilon_complex, dtype=complex),
            electric_field_distribution=self._make_field_distribution(outer_radius_m * 2, effective_length_m * 2, field_scale=float(abs(epsilon_complex))),
            metadata=self.metadata() | {"effective_probe_capacitance_f": c0},
            z0=self.z0,
        )

    def validate(self) -> list[str]:
        return [] if self.geometry.sensor_type == "open_ended_coax_probe" else ["Probe model is best paired with an OECP geometry profile."]

    def parameters(self) -> list[ParameterDefinition]:
        parameters: list[ParameterDefinition] = []
        for index, layer in enumerate(self.layer_stack.layers):
            if layer.role in {"material", "protective_layer", "sensor_layer"}:
                parameters.extend(
                    [
                        ParameterDefinition(f"{layer.name}_epsilon_real", f"layer_stack.layers.{index}.epsilon_real", 1.0, 120.0, layer.epsilon_real),
                        ParameterDefinition(f"{layer.name}_epsilon_imag", f"layer_stack.layers.{index}.epsilon_imag", 0.0, 30.0, max(layer.epsilon_imag, 0.05)),
                        ParameterDefinition(
                            f"{layer.name}_thickness_m",
                            f"layer_stack.layers.{index}.thickness_m",
                            1e-6,
                            0.02,
                            max(layer.thickness_m, 1e-5),
                        ),
                        ParameterDefinition(
                            f"{layer.name}_conductivity_s_per_m",
                            f"layer_stack.layers.{index}.conductivity_s_per_m",
                            0.0,
                            20.0,
                            max(layer.conductivity_s_per_m, 0.0),
                        ),
                    ]
                )
        return parameters

    def constraints(self) -> dict[str, float]:
        return {"min_points": 3}

    def metadata(self) -> dict[str, str]:
        return {
            "name": "Open Ended Coax Probe Model",
            "description": "Capacitive admittance model for multilayer OECP dielectric sensing.",
            "support_level": "research baseline",
            "future_integrations": ["HFSS", "COMSOL", "openEMS"],
        }
