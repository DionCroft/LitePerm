"""Forward electromagnetic model registry."""

from liteperm.inverse.forward_models.base import ForwardModel
from liteperm.inverse.forward_models.generic_resonator import GenericResonatorModel
from liteperm.inverse.forward_models.microstrip_resonator import MicrostripResonatorModel
from liteperm.inverse.forward_models.open_ended_coax_probe import OpenEndedCoaxProbeModel
from liteperm.inverse.forward_models.patch_antenna import PatchAntennaModel


def discover_forward_models() -> dict[str, type[ForwardModel]]:
    return {
        "patch_antenna": PatchAntennaModel,
        "open_ended_coax_probe": OpenEndedCoaxProbeModel,
        "microstrip_resonator": MicrostripResonatorModel,
        "generic_resonator": GenericResonatorModel,
    }


def build_forward_model(sensor_type: str, **kwargs) -> ForwardModel:
    registry = discover_forward_models()
    key = sensor_type.lower()
    if key not in registry:
        raise KeyError(f"Unknown forward model: {sensor_type}")
    return registry[key](**kwargs)


__all__ = [
    "ForwardModel",
    "GenericResonatorModel",
    "MicrostripResonatorModel",
    "OpenEndedCoaxProbeModel",
    "PatchAntennaModel",
    "build_forward_model",
    "discover_forward_models",
]

