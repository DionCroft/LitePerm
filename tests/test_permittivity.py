import numpy as np

from liteperm.geometry.profiles import build_geometry_profile
from liteperm.models.core import MeasurementData
from liteperm.transform.permittivity import available_methods, compute_material_spectrum


def test_available_methods():
    assert {"stuchly", "marsland", "komarov"} <= set(available_methods())


def test_compute_material_spectrum_returns_expected_shapes():
    measurement = MeasurementData(
        frequency_hz=np.array([1e6, 10e6, 100e6], dtype=float),
        s11=np.array([0.2 - 0.1j, 0.15 - 0.12j, 0.1 - 0.2j]),
    )
    geometry = build_geometry_profile("open_ended_coax_probe")

    spectrum, working_measurement = compute_material_spectrum(measurement, geometry, method="stuchly")

    assert spectrum.frequency_hz.shape == measurement.frequency_hz.shape
    assert spectrum.epsilon_complex.shape == measurement.s11.shape
    assert working_measurement.source_name == measurement.source_name

