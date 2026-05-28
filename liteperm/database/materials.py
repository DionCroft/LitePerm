"""SQLite-backed material library seeded from bundled reference data."""

from __future__ import annotations

import sqlite3
from pathlib import Path

from liteperm.utils.json_io import dumps_json
from liteperm.utils.paths import MATERIAL_DB_PATH, ensure_runtime_directories
from liteperm.utils.resources import load_reference_materials


class MaterialDatabase:
    def __init__(self, database_path: str | Path = MATERIAL_DB_PATH):
        ensure_runtime_directories()
        self.database_path = Path(database_path)
        self._initialise()
        self._seed_defaults()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialise(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS materials (
                    material_name TEXT PRIMARY KEY,
                    category TEXT,
                    epsilon_real REAL,
                    epsilon_imag REAL,
                    loss_tangent REAL,
                    conductivity_s_per_m REAL,
                    frequency_range_hz TEXT,
                    source TEXT,
                    reference_list TEXT,
                    notes TEXT,
                    payload_json TEXT NOT NULL
                )
                """
            )

    def _seed_defaults(self) -> None:
        materials = load_reference_materials()
        extras = {
            "saline": {
                "display_name": "Saline",
                "category": "liquid",
                "epsilon_real": 76.0,
                "epsilon_imag": 15.0,
                "loss_tangent": 0.197,
                "conductivity_s_per_m": 2.03,
                "reference_frequency_ghz": 2.45,
                "notes": "Representative saline reference for biomedical sensing.",
            },
            "nacl_solutions": {
                "display_name": "NaCl Solutions",
                "category": "liquid",
                "epsilon_real": 72.0,
                "epsilon_imag": 19.0,
                "loss_tangent": 0.264,
                "conductivity_s_per_m": 2.57,
                "reference_frequency_ghz": 2.45,
                "notes": "Generalised NaCl solution family entry for comparative concentration studies.",
            },
        }
        materials = {**materials, **extras}
        with self._connect() as connection:
            for key, payload in materials.items():
                connection.execute(
                    """
                    INSERT OR IGNORE INTO materials (
                        material_name, category, epsilon_real, epsilon_imag, loss_tangent,
                        conductivity_s_per_m, frequency_range_hz, source, reference_list, notes, payload_json
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        payload.get("display_name", key),
                        payload.get("category", ""),
                        payload.get("epsilon_real"),
                        payload.get("epsilon_imag"),
                        payload.get("loss_tangent"),
                        payload.get("conductivity_s_per_m"),
                        dumps_json([50e3, 6.3e9]),
                        payload.get("source", "LitePerm bundled library"),
                        payload.get("references", ""),
                        payload.get("notes", ""),
                        dumps_json(payload),
                    ),
                )

    def list_materials(self, *, search: str = "") -> list[dict[str, object]]:
        with self._connect() as connection:
            if search:
                rows = connection.execute(
                    "SELECT * FROM materials WHERE material_name LIKE ? OR category LIKE ? ORDER BY material_name",
                    (f"%{search}%", f"%{search}%"),
                ).fetchall()
            else:
                rows = connection.execute("SELECT * FROM materials ORDER BY material_name").fetchall()
        return [dict(row) for row in rows]

    def add_material(self, payload: dict[str, object]) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT OR REPLACE INTO materials (
                    material_name, category, epsilon_real, epsilon_imag, loss_tangent,
                    conductivity_s_per_m, frequency_range_hz, source, reference_list, notes, payload_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    str(payload.get("material_name") or payload.get("display_name")),
                    str(payload.get("category", "")),
                    payload.get("epsilon_real"),
                    payload.get("epsilon_imag"),
                    payload.get("loss_tangent"),
                    payload.get("conductivity_s_per_m"),
                    dumps_json(payload.get("frequency_range_hz", [50e3, 6.3e9])),
                    str(payload.get("source", "User")),
                    str(payload.get("references", "")),
                    str(payload.get("notes", "")),
                    dumps_json(payload),
                ),
            )
