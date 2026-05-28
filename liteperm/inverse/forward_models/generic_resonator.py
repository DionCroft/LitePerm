"""Generic resonator forward model for exploratory inverse studies."""

from __future__ import annotations

from liteperm.inverse.common import ParameterDefinition
from liteperm.inverse.forward_models.base import ForwardModel, dielectric_notch_q
from liteperm.utils.constants import TWO_PI


class GenericResonatorModel(ForwardModel):
    def simulate(self, frequency_hz):
        params = self.geometry.parameters
        effective_capacitance_pf = float(params.get("effective_capacitance_pf", 0.85))
        effective_volume_mm3 = float(params.get("effective_volume_mm3", 1000.0))
        epsilon_complex = self.layer_stack.effective_epsilon(decay_length_m=max(self.layer_stack.total_thickness_m(), 1e-4))
        effective_capacitance = effective_capacitance_pf * 1e-12 * max(epsilon_complex.real, 1e-6)
        inductance_h = max((effective_volume_mm3 * 1e-9), 1e-9)
        resonant_frequency_hz = 1.0 / max(TWO_PI * (inductance_h * effective_capacitance) ** 0.5, 1e-12)
        q_factor = dielectric_notch_q(45.0, epsilon_complex, sum(layer.conductivity_s_per_m for layer in self.layer_stack.layers), self.layer_stack.total_thickness_m())
        return self._series_resonator_simulation(
            frequency_hz=frequency_hz,
            resonant_frequency_hz=resonant_frequency_hz,
            q_factor=q_factor,
            resistance_ohm=self.z0,
            effective_permittivity_complex=epsilon_complex,
            width_m=(effective_volume_mm3 ** (1 / 3)) * 1e-3,
            length_m=(effective_volume_mm3 ** (1 / 3)) * 1e-3,
            coupling_depth=1.0,
            metadata=self.metadata(),
        )

    def validate(self) -> list[str]:
        return []

    def parameters(self) -> list[ParameterDefinition]:
        material_layer = self.layer_stack.layers[0] if self.layer_stack.layers else None
        return [
            ParameterDefinition(
                "effective_capacitance_pf",
                "geometry.parameters.effective_capacitance_pf",
                0.05,
                20.0,
                float(self.geometry.parameters.get("effective_capacitance_pf", 0.85)),
            ),
            ParameterDefinition(
                "material_epsilon_real",
                "layer_stack.layers.0.epsilon_real",
                1.0,
                120.0,
                material_layer.epsilon_real if material_layer is not None else 4.0,
            ),
            ParameterDefinition(
                "material_epsilon_imag",
                "layer_stack.layers.0.epsilon_imag",
                0.0,
                30.0,
                max(material_layer.epsilon_imag, 0.05) if material_layer is not None else 0.1,
            ),
            ParameterDefinition(
                "material_conductivity_s_per_m",
                "layer_stack.layers.0.conductivity_s_per_m",
                0.0,
                10.0,
                max(material_layer.conductivity_s_per_m, 0.0) if material_layer is not None else 0.0,
            ),
            ParameterDefinition(
                "material_thickness_m",
                "layer_stack.layers.0.thickness_m",
                1e-6,
                0.02,
                material_layer.thickness_m if material_layer is not None else 1e-3,
            ),
        ]

    def constraints(self) -> dict[str, float]:
        return {}

    def metadata(self) -> dict[str, str]:
        return {
            "name": "Generic Resonator Model",
            "description": "Generic lumped resonator model for exploratory inverse studies.",
            "support_level": "research baseline",
            "future_integrations": ["surrogate models", "openEMS"],
        }
