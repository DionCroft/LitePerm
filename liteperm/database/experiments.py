"""SQLite-backed experiment storage and project archiving."""

from __future__ import annotations

import shutil
import sqlite3
import uuid
from datetime import UTC, datetime
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

from liteperm.io.exporters import measurement_to_touchstone_bytes, spectrum_to_csv_bytes
from liteperm.models.core import (
    CalibrationProfile,
    ExperimentMetadata,
    ExperimentRecord,
    MaterialSpectrum,
    MeasurementData,
    SensorGeometryProfile,
)
from liteperm.reports.generator import generate_experiment_reports
from liteperm.utils.json_io import dumps_json, loads_json
from liteperm.utils.paths import EXPERIMENT_DB_PATH, PROJECTS_ROOT, ensure_runtime_directories
from liteperm.utils.yaml_io import dump_yaml
from liteperm.visualisation.plots import build_epsilon_plot, build_magnitude_plot, build_phase_plot, build_smith_chart


def _slugify(value: str) -> str:
    characters = [character.lower() if character.isalnum() else "_" for character in value.strip()]
    slug = "".join(characters).strip("_")
    while "__" in slug:
        slug = slug.replace("__", "_")
    return slug or "project"


class ExperimentDatabase:
    def __init__(self, database_path: str | Path = EXPERIMENT_DB_PATH):
        ensure_runtime_directories()
        self.database_path = Path(database_path)
        self._initialise()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialise(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS experiments (
                    experiment_id TEXT PRIMARY KEY,
                    experiment_name TEXT NOT NULL,
                    researcher TEXT,
                    project_name TEXT,
                    sensor_type TEXT,
                    material_under_test TEXT,
                    created_at TEXT,
                    tags TEXT,
                    metadata_json TEXT NOT NULL,
                    raw_measurement_json TEXT NOT NULL,
                    processed_measurement_json TEXT NOT NULL,
                    spectrum_json TEXT NOT NULL,
                    calibration_json TEXT NOT NULL,
                    geometry_json TEXT NOT NULL,
                    plot_manifest_json TEXT NOT NULL,
                    report_manifest_json TEXT NOT NULL,
                    inverse_result_json TEXT,
                    digital_twin_json TEXT,
                    project_directory TEXT NOT NULL
                )
                """
            )
            existing_columns = {row["name"] for row in connection.execute("PRAGMA table_info(experiments)").fetchall()}
            if "inverse_result_json" not in existing_columns:
                connection.execute("ALTER TABLE experiments ADD COLUMN inverse_result_json TEXT")
            if "digital_twin_json" not in existing_columns:
                connection.execute("ALTER TABLE experiments ADD COLUMN digital_twin_json TEXT")

    def _build_project_structure(self, metadata: ExperimentMetadata, experiment_id: str) -> dict[str, Path]:
        project_dir = PROJECTS_ROOT / _slugify(metadata.project_name) / experiment_id
        directories = {
            "root": project_dir,
            "raw": project_dir / "raw",
            "processed": project_dir / "processed",
            "plots": project_dir / "plots",
            "reports": project_dir / "reports",
            "metadata": project_dir / "metadata",
        }
        for directory in directories.values():
            directory.mkdir(parents=True, exist_ok=True)
        return directories

    def _write_plot_bundle(
        self,
        raw_measurement: MeasurementData,
        spectrum: MaterialSpectrum,
        output_dir: Path,
    ) -> dict[str, str]:
        plot_manifest: dict[str, str] = {}
        figures = {
            "s11_magnitude": build_magnitude_plot(raw_measurement),
            "s11_phase": build_phase_plot(raw_measurement),
            "smith_chart": build_smith_chart(raw_measurement),
            "permittivity": build_epsilon_plot(spectrum),
        }
        for name, figure in figures.items():
            target = output_dir / f"{name}.html"
            target.write_text(figure.to_html(full_html=True, include_plotlyjs="cdn"), encoding="utf-8")
            plot_manifest[name] = str(target)
        return plot_manifest

    def save_experiment(
        self,
        *,
        metadata: ExperimentMetadata,
        raw_measurement: MeasurementData,
        processed_measurement: MeasurementData,
        spectrum: MaterialSpectrum,
        calibration_profile: CalibrationProfile,
        geometry_profile: SensorGeometryProfile,
        inverse_result: dict | None = None,
        digital_twin: dict | None = None,
    ) -> ExperimentRecord:
        experiment_id = f"EXP-{datetime.now(UTC):%Y%m%d-%H%M%S}-{uuid.uuid4().hex[:8]}"
        directories = self._build_project_structure(metadata, experiment_id)

        (directories["raw"] / "raw_measurement.s1p").write_bytes(measurement_to_touchstone_bytes(raw_measurement))
        raw_measurement.to_dataframe().to_csv(directories["raw"] / "raw_measurement.csv", index=False)
        processed_measurement.to_dataframe().to_csv(directories["processed"] / "processed_measurement.csv", index=False)
        (directories["processed"] / "permittivity_spectrum.csv").write_bytes(spectrum_to_csv_bytes(spectrum))

        (directories["metadata"] / "experiment.yaml").write_text(dump_yaml(metadata.to_dict()), encoding="utf-8")
        (directories["metadata"] / "calibration.yaml").write_text(dump_yaml(calibration_profile.to_dict()), encoding="utf-8")
        (directories["metadata"] / "geometry.yaml").write_text(dump_yaml(geometry_profile.to_dict()), encoding="utf-8")

        record = ExperimentRecord(
            experiment_id=experiment_id,
            metadata=metadata,
            raw_measurement=raw_measurement,
            processed_measurement=processed_measurement,
            spectrum=spectrum,
            calibration_profile=calibration_profile,
            geometry_profile=geometry_profile,
            project_directory=str(directories["root"]),
            inverse_result=inverse_result,
            digital_twin=digital_twin,
        )
        record.plot_manifest = self._write_plot_bundle(raw_measurement, spectrum, directories["plots"])
        record.report_manifest = generate_experiment_reports(record, directories["reports"])
        if inverse_result is not None:
            (directories["metadata"] / "inverse_result.json").write_text(dumps_json(inverse_result, indent=2), encoding="utf-8")
        if digital_twin is not None:
            (directories["metadata"] / "digital_twin.json").write_text(dumps_json(digital_twin, indent=2), encoding="utf-8")

        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO experiments (
                    experiment_id, experiment_name, researcher, project_name, sensor_type,
                    material_under_test, created_at, tags, metadata_json, raw_measurement_json,
                    processed_measurement_json, spectrum_json, calibration_json, geometry_json,
                    plot_manifest_json, report_manifest_json, inverse_result_json, digital_twin_json, project_directory
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    experiment_id,
                    metadata.experiment_name,
                    metadata.researcher,
                    metadata.project_name,
                    metadata.sensor_type,
                    metadata.material_under_test,
                    metadata.created_at,
                    ",".join(metadata.tags),
                    dumps_json(metadata.to_dict()),
                    dumps_json(raw_measurement.to_dict()),
                    dumps_json(processed_measurement.to_dict()),
                    dumps_json(spectrum.to_dict()),
                    dumps_json(calibration_profile.to_dict()),
                    dumps_json(geometry_profile.to_dict()),
                    dumps_json(record.plot_manifest),
                    dumps_json(record.report_manifest),
                    dumps_json(inverse_result) if inverse_result is not None else None,
                    dumps_json(digital_twin) if digital_twin is not None else None,
                    str(directories["root"]),
                ),
            )
        return record

    def list_experiments(
        self,
        *,
        search: str = "",
        sensor_type: str = "",
        project_name: str = "",
        sort_by: str = "created_at",
        descending: bool = True,
    ) -> list[dict[str, str]]:
        order = "DESC" if descending else "ASC"
        if sort_by not in {"created_at", "experiment_name", "project_name", "researcher"}:
            sort_by = "created_at"

        clauses = []
        values: list[str] = []
        if search:
            clauses.append("(experiment_name LIKE ? OR researcher LIKE ? OR material_under_test LIKE ? OR tags LIKE ?)")
            token = f"%{search}%"
            values.extend([token, token, token, token])
        if sensor_type:
            clauses.append("sensor_type = ?")
            values.append(sensor_type)
        if project_name:
            clauses.append("project_name = ?")
            values.append(project_name)
        where_clause = f"WHERE {' AND '.join(clauses)}" if clauses else ""

        with self._connect() as connection:
            rows = connection.execute(
                f"SELECT * FROM experiments {where_clause} ORDER BY {sort_by} {order}",
                values,
            ).fetchall()
        return [dict(row) for row in rows]

    def get_experiment(self, experiment_id: str) -> ExperimentRecord:
        with self._connect() as connection:
            row = connection.execute("SELECT * FROM experiments WHERE experiment_id = ?", (experiment_id,)).fetchone()
        if row is None:
            raise KeyError(f"Unknown experiment id: {experiment_id}")
        payload = {
            "experiment_id": row["experiment_id"],
            "metadata": loads_json(row["metadata_json"]),
            "raw_measurement": loads_json(row["raw_measurement_json"]),
            "processed_measurement": loads_json(row["processed_measurement_json"]),
            "spectrum": loads_json(row["spectrum_json"]),
            "calibration_profile": loads_json(row["calibration_json"]),
            "geometry_profile": loads_json(row["geometry_json"]),
            "project_directory": row["project_directory"],
            "plot_manifest": loads_json(row["plot_manifest_json"]),
            "report_manifest": loads_json(row["report_manifest_json"]),
            "inverse_result": loads_json(row["inverse_result_json"]) if row["inverse_result_json"] else None,
            "digital_twin": loads_json(row["digital_twin_json"]) if row["digital_twin_json"] else None,
        }
        return ExperimentRecord.from_dict(payload)

    def delete_experiment(self, experiment_id: str) -> None:
        record = self.get_experiment(experiment_id)
        project_dir = Path(record.project_directory)
        if PROJECTS_ROOT in project_dir.parents:
            shutil.rmtree(project_dir, ignore_errors=True)
        with self._connect() as connection:
            connection.execute("DELETE FROM experiments WHERE experiment_id = ?", (experiment_id,))

    def duplicate_experiment(self, experiment_id: str) -> ExperimentRecord:
        record = self.get_experiment(experiment_id)
        duplicated_metadata = ExperimentMetadata.from_dict(record.metadata.to_dict())
        duplicated_metadata.experiment_name = f"{duplicated_metadata.experiment_name} Copy"
        duplicated_metadata.created_at = datetime.now(UTC).isoformat()
        return self.save_experiment(
            metadata=duplicated_metadata,
            raw_measurement=record.raw_measurement,
            processed_measurement=record.processed_measurement,
            spectrum=record.spectrum,
            calibration_profile=record.calibration_profile,
            geometry_profile=record.geometry_profile,
            inverse_result=record.inverse_result,
            digital_twin=record.digital_twin,
        )

    def export_experiment(self, experiment_id: str) -> bytes:
        record = self.get_experiment(experiment_id)
        project_dir = Path(record.project_directory)
        archive_path = project_dir / f"{experiment_id}.zip"
        with ZipFile(archive_path, "w", compression=ZIP_DEFLATED) as archive:
            for file_path in project_dir.rglob("*"):
                if file_path.is_file() and file_path != archive_path:
                    archive.write(file_path, file_path.relative_to(project_dir))
        return archive_path.read_bytes()
