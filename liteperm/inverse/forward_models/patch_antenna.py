"""Simplified first-principles patch antenna forward model."""

from __future__ import annotations

import numpy as np

from liteperm.inverse.common import ForwardSimulation, ParameterDefinition
from liteperm.inverse.forward_models.base import ForwardModel, dielectric_notch_q, microstrip_effective_permittivity, patch_resonant_frequency


class PatchAntennaModel(ForwardModel):
    def simulate(self, frequency_hz: np.ndarray) -> ForwardSimulation:
        params = self.geometry.parameters
        length_m = float(params.get("length_mm", 32.0)) * 1e-3
        width_m = float(params.get("width_mm", 38.0)) * 1e-3
        substrate_height_m = float(params.get("substrate_height_mm", 1.6)) * 1e-3
        substrate_er = float(params.get("substrate_permittivity", 4.3))
        feed_position_m = float(params.get("feed_position_mm", params.get("feed_offset_mm", 7.0))) * 1e-3
        external_er = self.layer_stack.effective_epsilon(decay_length_m=max(substrate_height_m * 3, 1e-4))
        effective_er = microstrip_effective_permittivity(substrate_er, substrate_height_m, width_m, external_er)
        resonant_frequency_hz = patch_resonant_frequency(length_m, substrate_height_m, effective_er)
        total_thickness_m = self.layer_stack.total_thickness_m()
        conductivity = sum(layer.conductivity_s_per_m for layer in self.layer_stack.layers)
        q_factor = dielectric_notch_q(65.0, effective_er, conductivity, total_thickness_m)
        coupling_depth = 1.0 + abs(feed_position_m / max(length_m / 2, 1e-6) - 0.5)
        resistance = self.z0 * (0.8 + 0.6 * coupling_depth)
        metadata = self.metadata() | {
            "effective_permittivity_real": effective_er.real,
            "effective_permittivity_imag": effective_er.imag,
            "predicted_material_thickness_m": total_thickness_m,
        }
        simulation = self._series_resonator_simulation(
            frequency_hz=frequency_hz,
            resonant_frequency_hz=resonant_frequency_hz,
            q_factor=q_factor,
            resistance_ohm=resistance,
            effective_permittivity_complex=effective_er,
            width_m=width_m,
            length_m=length_m,
            coupling_depth=coupling_depth,
            metadata=metadata,
        )
        return simulation

    def validate(self) -> list[str]:
        issues = []
        if self.geometry.sensor_type != "patch_antenna":
            issues.append("PatchAntennaModel is most appropriate for patch-antenna geometry profiles.")
        if not self.layer_stack.layers:
            issues.append("A layer stack is recommended for material-under-test estimation.")
        return issues

    def parameters(self) -> list[ParameterDefinition]:
        parameters = [
            ParameterDefinition("patch_length_mm", "geometry.parameters.length_mm", 10.0, 80.0, float(self.geometry.parameters.get("length_mm", 32.0))),
            ParameterDefinition("patch_width_mm", "geometry.parameters.width_mm", 10.0, 100.0, float(self.geometry.parameters.get("width_mm", 38.0))),
        ]
        if len(self.layer_stack.layers) >= 3:
            layer_index = 2 if self.layer_stack.layers[2].role == "material" else len(self.layer_stack.layers) - 1
            layer = self.layer_stack.layers[layer_index]
            parameters.extend(
                [
                    ParameterDefinition("material_epsilon_real", f"layer_stack.layers.{layer_index}.epsilon_real", 1.0, 120.0, layer.epsilon_real),
                    ParameterDefinition("material_epsilon_imag", f"layer_stack.layers.{layer_index}.epsilon_imag", 0.0, 30.0, max(layer.epsilon_imag, 0.1)),
                    ParameterDefinition(
                        "material_conductivity_s_per_m",
                        f"layer_stack.layers.{layer_index}.conductivity_s_per_m",
                        0.0,
                        10.0,
                        max(layer.conductivity_s_per_m, 0.0),
                    ),
                    ParameterDefinition(
                        "material_thickness_m",
                        f"layer_stack.layers.{layer_index}.thickness_m",
                        1e-5,
                        0.02,
                        max(layer.thickness_m, 1e-4),
                    ),
                ]
            )
        return parameters

    def constraints(self) -> dict[str, float]:
        return {"frequency_min_hz": 1e6, "frequency_max_hz": 6.3e9}

    def metadata(self) -> dict[str, str]:
        return {
            "name": "Patch Antenna Model",
            "description": "Simplified cavity-inspired patch antenna forward model with multilayer sensing stack support.",
            "support_level": "research baseline",
            "future_integrations": ["HFSS", "CST", "COMSOL", "openEMS", "Meep"],
        }

