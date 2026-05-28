"""Generate experiment reports in Markdown, HTML, and PDF formats."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from matplotlib.backends.backend_pdf import PdfPages

from liteperm.models.core import ExperimentRecord
from liteperm.visualisation.plots import build_static_measurement_preview, build_static_spectrum_preview


def _markdown_report(record: ExperimentRecord) -> str:
    metadata = record.metadata
    inverse_lines = []
    if record.inverse_result:
        inverse_lines.extend(["", "## Inverse Modelling Summary", ""])
        inverse_lines.append(f"- Solver: {record.inverse_result.get('solver_name', 'unknown')}")
        inverse_lines.append(f"- Objective: {record.inverse_result.get('objective_value', 'n/a')}")
        best_parameters = record.inverse_result.get("best_parameters", {})
        for key, value in best_parameters.items():
            inverse_lines.append(f"- {key}: {value}")
    return "\n".join(
        [
            f"# {metadata.experiment_name}",
            "",
            f"- Experiment ID: `{record.experiment_id}`",
            f"- Researcher: {metadata.researcher}",
            f"- Project: {metadata.project_name}",
            f"- Sensor Type: {metadata.sensor_type}",
            f"- Material Under Test: {metadata.material_under_test}",
            f"- Calibration Profile: {metadata.calibration_profile_name}",
            f"- Geometry Profile: {metadata.geometry_profile_name}",
            f"- Frequency Range (Hz): {metadata.frequency_range_hz[0]:.0f} to {metadata.frequency_range_hz[1]:.0f}",
            f"- Temperature (C): {metadata.temperature_c if metadata.temperature_c is not None else 'n/a'}",
            f"- Humidity (%): {metadata.humidity_percent if metadata.humidity_percent is not None else 'n/a'}",
            f"- Tags: {', '.join(metadata.tags) if metadata.tags else 'none'}",
            "",
            "## Description",
            "",
            metadata.description or "No description provided.",
            "",
            "## Notes",
            "",
            metadata.notes or "No notes provided.",
            "",
            "## Summary Statistics",
            "",
            f"- Mean epsilon': {record.spectrum.epsilon_prime.mean():.4f}",
            f"- Mean epsilon'': {record.spectrum.epsilon_double_prime.mean():.4f}",
            f"- Peak loss tangent: {record.spectrum.loss_tangent.max():.4f}",
            f"- Peak conductivity (S/m): {record.spectrum.conductivity_s_per_m.max():.4f}",
            *inverse_lines,
        ]
    )


def _html_report(record: ExperimentRecord) -> str:
    markdown = _markdown_report(record).replace("\n", "<br/>\n")
    return (
        "<html><head><title>LitePerm Experiment Report</title></head><body>"
        f"<h1>{record.metadata.experiment_name}</h1>"
        f"<div>{markdown}</div>"
        "</body></html>"
    )


def _pdf_report(record: ExperimentRecord, target_path: Path) -> None:
    with PdfPages(target_path) as pdf:
        text_figure = build_static_measurement_preview(record.raw_measurement)
        text_figure.suptitle(f"{record.metadata.experiment_name} - Raw S11")
        pdf.savefig(text_figure)
        text_figure.clf()

        spectrum_figure = build_static_spectrum_preview(record.spectrum)
        spectrum_figure.suptitle(f"{record.metadata.experiment_name} - Permittivity")
        pdf.savefig(spectrum_figure)
        spectrum_figure.clf()


def generate_experiment_reports(record: ExperimentRecord, output_dir: str | Path) -> dict[str, str]:
    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)

    markdown_path = destination / "report.md"
    html_path = destination / "report.html"
    pdf_path = destination / "report.pdf"

    markdown_path.write_text(_markdown_report(record), encoding="utf-8")
    html_path.write_text(_html_report(record), encoding="utf-8")
    _pdf_report(record, pdf_path)

    return {"markdown": str(markdown_path), "html": str(html_path), "pdf": str(pdf_path)}
