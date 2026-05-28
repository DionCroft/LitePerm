"""REST API for experiments, materials, profiles, sweeps, and plugins."""

from __future__ import annotations

from pathlib import Path

from liteperm.calibration.profiles import list_saved_calibration_profiles
from liteperm.database.experiments import ExperimentDatabase
from liteperm.database.materials import MaterialDatabase
from liteperm.devices.future_device import FutureDevice
from liteperm.geometry.profiles import list_saved_geometry_profiles
from liteperm.models.core import SweepConfig
from liteperm.plugins.manager import discover_plugins

try:  # pragma: no cover - optional runtime dependency
    from fastapi import FastAPI
except Exception:  # pragma: no cover - optional runtime dependency
    FastAPI = None


def create_api_app():
    if FastAPI is None:  # pragma: no cover - optional runtime dependency
        raise ImportError("FastAPI is not installed. Install dependencies from requirements.txt to use the API.")

    app = FastAPI(title="LitePerm API", version="0.2.0")
    experiments = ExperimentDatabase()
    materials = MaterialDatabase()

    @app.get("/")
    def root():
        return {"name": "LitePerm API", "version": "0.2.0"}

    @app.get("/experiments")
    def list_experiments():
        return experiments.list_experiments()

    @app.get("/experiments/{experiment_id}")
    def get_experiment(experiment_id: str):
        return experiments.get_experiment(experiment_id).to_dict()

    @app.get("/materials")
    def list_materials(search: str = ""):
        return materials.list_materials(search=search)

    @app.get("/calibrations")
    def list_calibrations():
        return list_saved_calibration_profiles()

    @app.get("/geometries")
    def list_geometries():
        return list_saved_geometry_profiles()

    @app.get("/plugins")
    def list_plugins():
        return {name: plugin.metadata() | {"description": plugin.description()} for name, plugin in discover_plugins().items()}

    @app.get("/sweeps")
    def preview_sweep(start_frequency_hz: float = 1e8, stop_frequency_hz: float = 6e9, points: int = 201):
        device = FutureDevice()
        device.connect()
        device.configure_sweep(SweepConfig(start_frequency_hz, stop_frequency_hz, points))
        measurement = device.capture_sweep()
        device.disconnect()
        return measurement.to_dict()

    return app
