from liteperm.ai.feature_extraction import extract_spectrum_features
from liteperm.geometry.profiles import build_geometry_profile
from liteperm.models.core import MeasurementData
from liteperm.transform.permittivity import compute_material_spectrum


def test_extract_spectrum_features_returns_expected_keys():
    measurement = MeasurementData(
        frequency_hz=[1e8, 2e8, 3e8, 4e8],
        s11=[0.8 - 0.1j, 0.4 - 0.25j, 0.5 - 0.2j, 0.6 - 0.1j],
    )
    spectrum, _ = compute_material_spectrum(measurement, build_geometry_profile("open_ended_coax_probe"))
    features = extract_spectrum_features(measurement, spectrum)

    assert "resonant_frequency_hz" in features
    assert "q_factor" in features
    assert "epsilon_prime_mean" in features
