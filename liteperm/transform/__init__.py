"""Network and dielectric transform helpers."""

from liteperm.transform.network import admittance_to_impedance, gamma_to_admittance, gamma_to_impedance


def available_methods():
    from liteperm.transform.permittivity import available_methods as _available_methods

    return _available_methods()


def compute_material_spectrum(*args, **kwargs):
    from liteperm.transform.permittivity import compute_material_spectrum as _compute_material_spectrum

    return _compute_material_spectrum(*args, **kwargs)


__all__ = ["admittance_to_impedance", "available_methods", "compute_material_spectrum", "gamma_to_admittance", "gamma_to_impedance"]
