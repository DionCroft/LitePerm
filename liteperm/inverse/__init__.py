"""Inverse electromagnetic modelling framework for LitePerm."""

from liteperm.inverse.common import (
    DigitalTwin,
    ForwardSimulation,
    InverseProblem,
    InverseResult,
    LayerDefinition,
    LayerStack,
    ParameterDefinition,
    ParameterSweepResult,
    SensitivityResult,
    UncertaintySummary,
    ValidationReport,
)
from liteperm.inverse.digital_twin import build_digital_twin


def build_forward_model(*args, **kwargs):
    from liteperm.inverse.forward_models import build_forward_model as _build_forward_model

    return _build_forward_model(*args, **kwargs)


def discover_forward_models(*args, **kwargs):
    from liteperm.inverse.forward_models import discover_forward_models as _discover_forward_models

    return _discover_forward_models(*args, **kwargs)


def build_inverse_solver(*args, **kwargs):
    from liteperm.inverse.inverse_solvers import build_inverse_solver as _build_inverse_solver

    return _build_inverse_solver(*args, **kwargs)


def discover_inverse_solvers(*args, **kwargs):
    from liteperm.inverse.inverse_solvers import discover_inverse_solvers as _discover_inverse_solvers

    return _discover_inverse_solvers(*args, **kwargs)

__all__ = [
    "DigitalTwin",
    "ForwardSimulation",
    "InverseProblem",
    "InverseResult",
    "LayerDefinition",
    "LayerStack",
    "ParameterDefinition",
    "ParameterSweepResult",
    "SensitivityResult",
    "UncertaintySummary",
    "ValidationReport",
    "build_digital_twin",
    "build_forward_model",
    "build_inverse_solver",
    "discover_forward_models",
    "discover_inverse_solvers",
]
