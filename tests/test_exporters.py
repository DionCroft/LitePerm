import plotly.graph_objects as go

from liteperm.geometry.profiles import build_geometry_profile
from liteperm.io.exporters import object_to_yaml_bytes, spectrum_to_csv_bytes
from liteperm.models.core import MeasurementData
from liteperm.transform.permittivity import compute_material_spectrum


def test_spectrum_csv_export_contains_expected_headers():
    measurement = MeasurementData(
        frequency_hz=[1e6, 10e6, 100e6],
        s11=[0.2 - 0.1j, 0.15 - 0.12j, 0.1 - 0.2j],
    )
    geometry = build_geometry_profile("generic_resonator")
    spectrum, _ = compute_material_spectrum(measurement, geometry)

    payload = spectrum_to_csv_bytes(spectrum).decode("utf-8")
    assert "epsilon_prime" in payload
    assert "conductivity_s_per_m" in payload


def test_yaml_export_for_geometry_profile():
    profile = build_geometry_profile("patch_antenna")
    payload = object_to_yaml_bytes(profile).decode("utf-8")
    assert "sensor_type" in payload
    assert "patch_antenna" in payload

