from pathlib import Path

import numpy as np

from liteperm.geometry.profiles import build_geometry_profile
from liteperm.inverse.forward_models import build_forward_model
from liteperm.inverse.service import default_layer_stack
from liteperm.io.exporters import measurement_to_touchstone_bytes
from liteperm.models.core import MeasurementData, SweepConfig
from liteperm.solvers import solver_status_rows
from liteperm.solvers.exporters import export_csv, export_touchstone
from liteperm.solvers.job import SimulationJob
from liteperm.solvers.openems_adapter import OpenEMSAdapter
from liteperm.solvers.result import SimulationResult
from liteperm.solvers import utils as solver_utils
from liteperm.solvers.utils import cache_directory, simulation_cache_key, sweep_config_from_frequency_axis


def test_simulation_job_round_trip_and_frequency_axis(tmp_path):
    geometry = build_geometry_profile("patch_antenna")
    layer_stack = default_layer_stack("patch_antenna")
    sweep = SweepConfig(start_frequency_hz=2.2e9, stop_frequency_hz=2.6e9, points=11)

    job = SimulationJob.from_sweep_config(
        job_id="job-001",
        solver_name="openems",
        sensor_type="patch_antenna",
        geometry_profile=geometry,
        material_stack=layer_stack,
        sweep_config=sweep,
        output_directory=tmp_path,
        mesh_settings={"quality": "medium"},
        boundary_conditions={"x": "PML"},
        excitation_settings={"output_power": 0},
        notes="unit test",
    )

    round_trip = SimulationJob.from_dict(job.to_dict())

    assert round_trip.job_id == "job-001"
    assert round_trip.output_path == tmp_path
    assert round_trip.frequency_axis_hz.shape == (11,)
    assert round_trip.frequency_axis_hz[0] == sweep.start_frequency_hz


def test_simulation_result_round_trip_and_exports(tmp_path):
    measurement = MeasurementData(
        frequency_hz=np.linspace(1.0e9, 2.0e9, 9),
        s11=np.linspace(0.1, 0.9, 9) * np.exp(1j * np.linspace(0.0, np.pi / 4, 9)),
        source_name="synthetic",
    )
    result = SimulationResult.from_measurement(
        measurement,
        solver_metadata={"solver_name": "openems", "effective_epsilon_real": 3.2},
        runtime_seconds=1.25,
    )

    touchstone_path = export_touchstone(result, tmp_path / "result.s1p")
    csv_path = export_csv(result, tmp_path / "result.csv")
    round_trip = SimulationResult.from_dict(result.to_dict())

    assert touchstone_path.exists()
    assert csv_path.exists()
    assert round_trip.frequency_hz.shape == measurement.frequency_hz.shape
    assert round_trip.to_material_spectrum().impedance.shape == measurement.frequency_hz.shape


def test_solver_status_rows_include_supported_registry_entries():
    rows = solver_status_rows()
    names = {row["solver"] for row in rows}

    assert {"openems", "meep", "hfss", "cst", "comsol"}.issubset(names)


def test_openems_adapter_reports_missing_environment(monkeypatch, tmp_path):
    adapter = OpenEMSAdapter()
    monkeypatch.setattr(adapter, "_find_executable", lambda: "")
    geometry = build_geometry_profile("patch_antenna")
    layer_stack = default_layer_stack("patch_antenna")
    sweep = SweepConfig(start_frequency_hz=2.3e9, stop_frequency_hz=2.5e9, points=21)

    job = adapter.build_job(geometry, layer_stack, sweep, tmp_path)
    environment = adapter.validate_environment()

    assert environment["status"] == "missing"
    try:
        adapter.run(job)
    except RuntimeError as error:
        assert "openEMS is not installed" in str(error)
    else:  # pragma: no cover - defensive
        raise AssertionError("Expected openEMS adapter run() to fail when the executable is unavailable.")


def test_openems_adapter_parses_cached_touchstone_result(tmp_path):
    adapter = OpenEMSAdapter()
    geometry = build_geometry_profile("patch_antenna")
    layer_stack = default_layer_stack("patch_antenna")
    sweep = SweepConfig(start_frequency_hz=2.3e9, stop_frequency_hz=2.5e9, points=5)
    job = adapter.build_job(geometry, layer_stack, sweep, tmp_path, cache_key="cached-test")

    measurement = MeasurementData(
        frequency_hz=np.linspace(2.3e9, 2.5e9, 5),
        s11=np.asarray([0.1 + 0.01j, 0.08 + 0.03j, 0.05 + 0.02j, 0.07 + 0.01j, 0.09 + 0.0j]),
        source_name="cached-touchstone",
    )
    (tmp_path / "simulated_response.s1p").write_bytes(measurement_to_touchstone_bytes(measurement))

    result = adapter.parse_results(job)

    assert np.allclose(result.s11, measurement.s11)
    assert result.touchstone_export_path.endswith(".s1p")


def test_cache_key_changes_when_geometry_changes():
    geometry_a = build_geometry_profile("patch_antenna")
    geometry_b = build_geometry_profile("patch_antenna", parameters={**build_geometry_profile("patch_antenna").parameters, "length_mm": 34.0})
    layer_stack = default_layer_stack("patch_antenna")
    sweep = SweepConfig(start_frequency_hz=2.3e9, stop_frequency_hz=2.5e9, points=41)

    key_a = simulation_cache_key(
        solver_name="openems",
        sensor_type="patch_antenna",
        geometry_profile=geometry_a,
        material_stack=layer_stack,
        sweep_config=sweep,
    )
    key_b = simulation_cache_key(
        solver_name="openems",
        sensor_type="patch_antenna",
        geometry_profile=geometry_b,
        material_stack=layer_stack,
        sweep_config=sweep,
    )

    assert key_a != key_b


def test_full_wave_forward_model_analytical_backend_simulates():
    geometry = build_geometry_profile("patch_antenna")
    layer_stack = default_layer_stack("patch_antenna")
    model = build_forward_model(
        "full_wave",
        geometry=geometry,
        layer_stack=layer_stack,
        metadata_overrides={"simulation_backend": "analytical"},
    )

    simulation = model.simulate(np.linspace(2.2e9, 2.7e9, 51))

    assert simulation.frequency_hz.shape == (51,)
    assert simulation.metadata["forward_backend"] == "analytical"
    assert simulation.predicted_resonant_frequency_hz > 0


def test_full_wave_forward_model_cached_backend_uses_cached_result(tmp_path, monkeypatch):
    geometry = build_geometry_profile("patch_antenna")
    layer_stack = default_layer_stack("patch_antenna")
    frequency_hz = np.linspace(2.3e9, 2.5e9, 9)
    sweep = sweep_config_from_frequency_axis(frequency_hz)
    project_name = "solver_cache_test"
    monkeypatch.setattr(solver_utils, "PROJECTS_ROOT", tmp_path)
    cache_key = simulation_cache_key(
        solver_name="openems",
        sensor_type="patch_antenna",
        geometry_profile=geometry,
        material_stack=layer_stack,
        sweep_config=sweep,
        mesh_settings={"quality": "medium", "cells_per_wavelength": 20},
        boundary_conditions={"x": "PML", "y": "PML", "z": "PML"},
        excitation_settings={"output_power": 0},
    )
    output_dir = cache_directory(project_name, cache_key)
    measurement = MeasurementData(
        frequency_hz=frequency_hz,
        s11=np.linspace(0.12, 0.04, frequency_hz.size) * np.exp(1j * np.linspace(0.0, 0.4, frequency_hz.size)),
        source_name="cached-full-wave",
    )
    cached_result = SimulationResult.from_measurement(
        measurement,
        solver_metadata={"solver_name": "openems", "cache_key": cache_key, "effective_epsilon_real": 4.4},
        runtime_seconds=0.2,
        touchstone_export_path=str(output_dir / "simulated_response.s1p"),
        csv_export_path=str(output_dir / "simulated_response.csv"),
    )
    (output_dir / "simulation_result.json").write_text(__import__("json").dumps(cached_result.to_dict()), encoding="utf-8")

    model = build_forward_model(
        "full_wave",
        geometry=geometry,
        layer_stack=layer_stack,
        metadata_overrides={
            "simulation_backend": "cached",
            "solver_name": "openems",
            "project_name": project_name,
            "mesh_settings": {"quality": "medium", "cells_per_wavelength": 20},
            "boundary_conditions": {"x": "PML", "y": "PML", "z": "PML"},
            "excitation_settings": {"output_power": 0},
        },
    )

    simulation = model.simulate(frequency_hz)

    assert np.allclose(simulation.s11, measurement.s11)
    assert simulation.metadata["solver_name"] == "openems"


def test_app_import_with_solver_layer():
    import app  # noqa: F401

    assert Path("app.py").exists()
