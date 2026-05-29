# Changelog

## v0.5.0

- Added the Phase 4 full-wave solver integration layer
- Added `liteperm/solvers` with solver adapters, registry, cache helpers, exporters, validators, and result models
- Added `SimulationJob` and `SimulationResult` models for reproducible simulation workflows
- Added the `Full-Wave Simulation` Streamlit tab with solver status, setup, result export, and measured-versus-simulated comparison
- Added a `FullWaveForwardModel` path so inverse modelling can use analytical, cached, and solver-backed forward responses
- Added openEMS adapter scaffolding, Meep adapter scaffolding, and example simulation job files
- Added full-wave solver documentation, setup guides, and simulation workflow pages to the MkDocs site
- Updated the README, roadmap, and release notes for the Phase 4 simulation-assisted workflow

## v0.4.0

- Added a full MkDocs Material documentation portal for GitHub Pages
- Added GitHub Pages deployment automation through `.github/workflows/docs.yml`
- Added beginner-focused installation guides for Windows 11, Ubuntu, and WSL2
- Added a browser-only Plotly.js demonstration for Touchstone and CSV visualisation
- Added browser connectivity investigation notes for Web Serial and WebUSB
- Added screenshot placeholders, research showcase pages, downloads page, and citation metadata

## v0.3.0

- Added the Phase 3 inverse electromagnetic modelling engine and Streamlit workflow
- Added forward models for patch antennas, open-ended coax probes, microstrip resonators, and generic resonators
- Added inverse solvers including least-squares, differential evolution, particle swarm, Bayesian-style search, and MCMC
- Added uncertainty quantification, sensitivity analysis, parameter sweeps, and inverse visualisations
- Added synthetic measurement generation and digital twin persistence for inverse runs
- Added experiment round-tripping for inverse results and digital twin snapshots

## v0.2.0

- Added device integration architecture with LiteVNA and simulated backends
- Added live sweep acquisition pipeline
- Added experiment storage, project archiving, and report generation
- Added plugin-based transformation discovery
- Added sensor model framework
- Added material database and experiment explorer
- Added AI-preparation modules and FastAPI service scaffolding
- Added GitHub collaboration templates and CI scaffolding

## v0.1.0

- Initial Streamlit dashboard
- Touchstone and CSV import
- S11, impedance, admittance, and dielectric-spectrum visualisation
- Calibration and geometry profile support
