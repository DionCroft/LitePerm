# Research Mode Guide

Research Mode stores measurements as structured experiments for long-term scientific traceability.

## What Gets Stored

- raw S11 Touchstone export
- raw and processed CSV files
- dielectric spectrum CSV
- plot HTML files
- Markdown, HTML, and PDF reports
- YAML metadata, calibration, and geometry snapshots
- SQLite experiment records
- inverse result and digital twin snapshots when available

## Typical Workflow

1. Import or capture a measurement.
2. Configure calibration and geometry.
3. Compute dielectric properties or run inverse estimation.
4. Enter experiment metadata.
5. Save the experiment.
6. Re-open, duplicate, export, or delete it from `Experiment Explorer`.
