from pathlib import Path

import numpy as np

from liteperm.io.parsers import load_measurement, parse_csv, parse_touchstone


EXAMPLE_ROOT = Path(__file__).resolve().parents[1] / "examples"


def test_parse_touchstone_example():
    measurement = parse_touchstone(EXAMPLE_ROOT / "sample_touchstone.s1p")
    assert measurement.frequency_hz.size == 10
    assert np.isclose(measurement.s11[0].real, 0.995796)
    assert np.isclose(measurement.s11[-1].imag, -0.595966)


def test_parse_csv_example():
    measurement = parse_csv(EXAMPLE_ROOT / "sample_litevna.csv")
    assert measurement.frequency_hz[0] == 1e8
    assert measurement.frequency_hz[-1] == 6e9
    assert np.all(np.abs(measurement.s11) < 1.0)


def test_load_measurement_dispatch():
    touchstone = load_measurement(EXAMPLE_ROOT / "sample_touchstone.s1p")
    csv = load_measurement(EXAMPLE_ROOT / "sample_litevna.csv")
    assert touchstone.metadata["format"] == "touchstone"
    assert csv.metadata["format"] == "csv"
