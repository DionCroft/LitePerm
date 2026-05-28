from pathlib import Path

from liteperm.calibration.profiles import build_calibration_profile
from liteperm.database.experiments import ExperimentDatabase
from liteperm.database.materials import MaterialDatabase
from liteperm.geometry.profiles import build_geometry_profile
from liteperm.models.core import ExperimentMetadata, MeasurementData
from liteperm.transform.permittivity import compute_material_spectrum


def test_material_database_seeds_defaults(tmp_path):
    database = MaterialDatabase(tmp_path / "materials.db")
    rows = database.list_materials()
    assert any(row["material_name"] == "Water" for row in rows)


def test_experiment_database_save_and_fetch(tmp_path, monkeypatch):
    monkeypatch.setattr("liteperm.database.experiments.PROJECTS_ROOT", tmp_path / "Projects")
    database = ExperimentDatabase(tmp_path / "experiments.db")
    calibration = build_calibration_profile("Test Calibration")
    geometry = build_geometry_profile("open_ended_coax_probe")
    measurement = MeasurementData(
        frequency_hz=[1e8, 2e8, 3e8],
        s11=[0.8 - 0.1j, 0.6 - 0.2j, 0.5 - 0.25j],
        source_name="Unit Test Sweep",
    )
    spectrum, processed = compute_material_spectrum(measurement, geometry)
    metadata = ExperimentMetadata(
        experiment_name="Experiment One",
        researcher="Tester",
        project_name="Project Alpha",
        sensor_type=geometry.sensor_type,
        calibration_profile_name=calibration.name,
        geometry_profile_name=geometry.name,
        frequency_range_hz=(1e8, 3e8),
        material_under_test="Water",
    )
    record = database.save_experiment(
        metadata=metadata,
        raw_measurement=measurement,
        processed_measurement=processed,
        spectrum=spectrum,
        calibration_profile=calibration,
        geometry_profile=geometry,
        inverse_result={"solver_name": "Least Squares", "best_parameters": {"material_epsilon_real": 4.5}},
        digital_twin={"twin_id": "TWIN-UNITTEST", "layer_stack": {"layers": [], "metadata": {}}},
    )

    fetched = database.get_experiment(record.experiment_id)
    assert fetched.metadata.experiment_name == "Experiment One"
    assert Path(fetched.project_directory).exists()
    assert fetched.inverse_result["best_parameters"]["material_epsilon_real"] == 4.5
    assert fetched.digital_twin["twin_id"] == "TWIN-UNITTEST"
