"""Simplified microstrip resonator forward model."""

from __future__ import annotations

from liteperm.inverse.common import ParameterDefinition
from liteperm.inverse.forward_models.base import ForwardModel, dielectric_notch_q, microstrip_effective_permittivity, quarter_wave_resonant_frequency


class MicrostripResonatorModel(ForwardModel):
    def simulate(self, frequency_hz):
        params = self.geometry.parameters
        line_length_m = float(params.get("line_length_mm", 42.0)) * 1e-3
        line_width_m = float(params.get("line_width_mm", 3.2)) * 1e-3
        substrate_height_m = float(params.get("substrate_height_mm", 1.6)) * 1e-3
        substrate_er = float(params.get("substrate_permittivity", 3.48))
        coupling_gap_mm = float(params.get("coupling_gap_mm", 0.4))
        external_er = self.layer_stack.effective_epsilon(decay_length_m=max(substrate_height_m * 3, 1e-4))
        effective_er = microstrip_effective_permittivity(substrate_er, substrate_height_m, line_width_m, external_er)
        resonant_frequency_hz = quarter_wave_resonant_frequency(line_length_m, effective_er)
        conductivity = sum(layer.conductivity_s_per_m for layer in self.layer_stack.layers)
        q_factor = dielectric_notch_q(80.0, effective_er, conductivity, self.layer_stack.total_thickness_m())
        resistance = self.z0 * (1.0 + coupling_gap_mm / 2.0)
        return self._series_resonator_simulation(
            frequency_hz=frequency_hz,
            resonant_frequency_hz=resonant_frequency_hz,
            q_factor=q_factor,
            resistance_ohm=resistance,
            effective_permittivity_complex=effective_er,
            width_m=line_width_m,
            length_m=line_length_m,
            coupling_depth=1.1,
            metadata=self.metadata(),
        )

    def validate(self) -> list[str]:
        return [] if self.geometry.sensor_type == "microstrip_resonator" else ["Microstrip model is best paired with a microstrip resonator geometry."]

    def parameters(self) -> list[ParameterDefinition]:
        material_index = 2 if len(self.layer_stack.layers) > 2 else 0
        material_layer = self.layer_stack.layers[material_index] if self.layer_stack.layers else None
        return [
            ParameterDefinition("line_length_mm", "geometry.parameters.line_length_mm", 10.0, 100.0, float(self.geometry.parameters.get("line_length_mm", 42.0))),
            ParameterDefinition("line_width_mm", "geometry.parameters.line_width_mm", 0.5, 15.0, float(self.geometry.parameters.get("line_width_mm", 3.2))),
            ParameterDefinition(
                "material_epsilon_real",
                f"layer_stack.layers.{material_index}.epsilon_real",
                1.0,
                120.0,
                material_layer.epsilon_real if material_layer is not None else 4.0,
            ),
            ParameterDefinition(
                "material_epsilon_imag",
                f"layer_stack.layers.{material_index}.epsilon_imag",
                0.0,
                30.0,
                max(material_layer.epsilon_imag, 0.05) if material_layer is not None else 0.1,
            ),
            ParameterDefinition(
                "material_conductivity_s_per_m",
                f"layer_stack.layers.{material_index}.conductivity_s_per_m",
                0.0,
                10.0,
                max(material_layer.conductivity_s_per_m, 0.0) if material_layer is not None else 0.0,
            ),
            ParameterDefinition(
                "material_thickness_m",
                f"layer_stack.layers.{material_index}.thickness_m",
                1e-6,
                0.02,
                material_layer.thickness_m if material_layer is not None else 1e-3,
            ),
        ]

    def constraints(self) -> dict[str, float]:
        return {"frequency_min_hz": 1e6, "frequency_max_hz": 10e9}

    def metadata(self) -> dict[str, str]:
        return {
            "name": "Microstrip Resonator Model",
            "description": "Quarter-wave microstrip resonator model with effective-permittivity loading.",
            "support_level": "research baseline",
            "future_integrations": ["openEMS", "Meep", "HFSS"],
        }
