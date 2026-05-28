import numpy as np

from liteperm.calibration.one_port import apply_one_port_calibration, solve_one_port_error_terms
from liteperm.models.core import MeasurementData


def test_one_port_identity_calibration():
    frequency = np.array([1e6, 10e6, 100e6], dtype=float)
    open_measurement = MeasurementData(frequency, np.array([1.0 + 0j, 1.0 + 0j, 1.0 + 0j]))
    short_measurement = MeasurementData(frequency, np.array([-1.0 + 0j, -1.0 + 0j, -1.0 + 0j]))
    load_measurement = MeasurementData(frequency, np.array([0.0 + 0j, 0.0 + 0j, 0.0 + 0j]))
    dut = MeasurementData(frequency, np.array([0.2 - 0.1j, 0.15 - 0.2j, -0.05 - 0.25j]))

    corrected, terms = apply_one_port_calibration(dut, open_measurement, short_measurement, load_measurement)

    assert np.allclose(corrected.s11, dut.s11)
    assert np.allclose(terms.directivity, 0.0)
    assert np.allclose(terms.reflection_tracking, 1.0)
    assert np.allclose(terms.source_match, 0.0)


def test_solve_error_terms_shape():
    frequency = np.array([1e6, 10e6], dtype=float)
    open_measurement = MeasurementData(frequency, np.array([0.95 + 0.01j, 0.96 + 0.01j]))
    short_measurement = MeasurementData(frequency, np.array([-0.93 + 0.01j, -0.94 + 0.01j]))
    load_measurement = MeasurementData(frequency, np.array([0.02 + 0.01j, 0.02 + 0.01j]))

    terms = solve_one_port_error_terms(open_measurement, short_measurement, load_measurement)

    assert terms.frequency_hz.shape == frequency.shape
    assert terms.directivity.shape == frequency.shape

