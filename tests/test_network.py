import numpy as np

from liteperm.transform.network import gamma_to_admittance, gamma_to_impedance, impedance_to_gamma


def test_gamma_impedance_round_trip():
    gamma = np.array([0.2 - 0.1j, -0.1 - 0.2j, 0.0 + 0.0j])
    impedance = gamma_to_impedance(gamma, z0=50.0)
    reconstructed = impedance_to_gamma(impedance, z0=50.0)
    assert np.allclose(reconstructed, gamma)


def test_gamma_to_admittance_behaviour():
    gamma = np.array([0.0 + 0.0j])
    admittance = gamma_to_admittance(gamma, z0=50.0)
    assert np.isclose(admittance[0], 0.02 + 0.0j)

