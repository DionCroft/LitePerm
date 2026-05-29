import numpy as np

from liteperm.database.materials import MaterialDatabase
from liteperm.geometry.profiles import build_geometry_profile
from liteperm.models.core import MaterialSpectrum, MeasurementData
from liteperm.permittivity import compare_to_reference_materials, run_permittivity_measurement, validate_permittivity_measurement


def build_reference_spectrum(*, epsilon_real: float, epsilon_imag: float) -> MaterialSpectrum:
    frequency_hz = np.linspace(1.0e9, 3.0e9, 5)
    epsilon_complex = np.full(frequency_hz.shape, epsilon_real - 1j * epsilon_imag, dtype=complex)
    impedance = np.full(frequency_hz.shape, 50.0 + 1j * 3.0, dtype=complex)
    admittance = 1.0 / impedance
    gamma = np.full(frequency_hz.shape, 0.15 - 0.04j, dtype=complex)
    conductivity = np.full(frequency_hz.shape, 0.02, dtype=float)
    loss_tangent = np.full(frequency_hz.shape, max(epsilon_imag / max(epsilon_real, 1e-6), 0.0), dtype=float)
    return MaterialSpectrum(
        frequency_hz=frequency_hz,
        epsilon_complex=epsilon_complex,
        impedance=impedance,
        admittance=admittance,
        gamma=gamma,
        conductivity_s_per_m=conductivity,
        loss_tangent=loss_tangent,
        method="unit-test",
    )


def test_run_permittivity_measurement_returns_validation_and_material_matches():
    measurement = MeasurementData(
        frequency_hz=np.array([1e8, 2e8, 3e8, 4e8], dtype=float),
        s11=np.array([0.65 - 0.05j, 0.58 - 0.08j, 0.52 - 0.10j, 0.47 - 0.11j]),
        source_name="Unit Test Measurement",
    )
    geometry = build_geometry_profile("open_ended_coax_probe")

    result = run_permittivity_measurement(measurement, geometry, method="stuchly")

    assert result.spectrum.frequency_hz.shape == measurement.frequency_hz.shape
    assert result.processed_measurement.frequency_hz.shape == measurement.frequency_hz.shape
    assert result.validation.confidence_label in {"Low", "Medium", "High"}
    assert result.reference_comparisons
    assert result.identified_materials


def test_material_database_payload_access_and_reference_matching(tmp_path):
    database = MaterialDatabase(tmp_path / "materials.db")
    water = database.get_material("Water")

    assert water is not None
    assert water["display_name"] == "Water"

    spectrum = build_reference_spectrum(epsilon_real=78.0, epsilon_imag=9.0)
    comparisons = compare_to_reference_materials(spectrum, database.list_material_payloads())

    assert comparisons[0]["display_name"] == "Water"
    assert comparisons[0]["similarity_score"] >= comparisons[-1]["similarity_score"]


def test_validation_flags_physically_implausible_spectrum_as_low_confidence():
    measurement = MeasurementData(
        frequency_hz=np.array([1e8, 2e8, 3e8], dtype=float),
        s11=np.array([0.95 + 0.95j, -0.90 + 0.85j, 0.88 - 0.92j]),
        source_name="Noisy Measurement",
    )
    bad_spectrum = MaterialSpectrum(
        frequency_hz=measurement.frequency_hz,
        epsilon_complex=np.array([220 - 1j * 140, -12 - 1j * 90, 310 - 1j * 200], dtype=complex),
        impedance=np.array([5 + 40j, 3 + 50j, 2 + 60j], dtype=complex),
        admittance=np.array([0.01 - 0.02j, 0.02 - 0.03j, 0.04 - 0.02j], dtype=complex),
        gamma=measurement.s11,
        conductivity_s_per_m=np.array([80.0, 95.0, 120.0], dtype=float),
        loss_tangent=np.array([7.0, 9.0, 12.0], dtype=float),
        method="unit-test",
    )

    validation = validate_permittivity_measurement(bad_spectrum, measurement)

    assert validation.confidence_label == "Low"
    assert validation.confidence_score < 50
