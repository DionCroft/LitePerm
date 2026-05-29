# LitePerm

<p align="center">
  <img src="docs/images/liteperm_logo.svg" alt="LitePerm Logo" width="360"/>
</p>

<p align="center">
  <strong>Open-source permittivity measurement platform for LiteVNA-based dielectric spectroscopy, material characterisation, and advanced RF modelling</strong>
</p>

<p align="center">
  LiteVNA | Calibration Wizard | Permittivity Measurement | Validation | Inverse Modelling | Full-Wave Simulation | Research Data Management
</p>

---

## Overview

LitePerm is an open-source Python platform focused on one primary outcome:

> Measure complex permittivity using LiteVNA hardware.

Phase 5 refactors LitePerm so it behaves more like a scientific instrument than a generic RF dashboard. The main workflow is now:

`Connect LiteVNA -> Select Sensor -> Run Calibration -> Measure Material -> Calculate epsilon' and epsilon'' -> Save Experiment`

LitePerm still includes the broader Phase 1 to Phase 4 RF and modelling stack, but the default user experience is now centred on:

- LiteVNA-first measurement workflows
- calibration-guided permittivity extraction
- probe-centric sensor setup
- validation-aware dielectric spectroscopy
- reference-material comparison
- research-grade experiment storage
- advanced inverse and full-wave modelling when required

LitePerm is designed for academic labs, engineering teams, postgraduate research, and collaborators who need a transparent alternative to closed VNA analysis software.

## Current Status

LitePerm currently includes implemented work from:

- Phase 1: dielectric spectroscopy dashboard
- Phase 2: device integration, research mode, and experiment storage
- Phase 3: inverse electromagnetic modelling
- Phase 4: full-wave solver integration layer
- Phase 5: plug-and-play permittivity measurement workflow

Latest major capabilities:

- Basic Mode and Advanced Mode
- measurement-first dashboard navigation
- calibration wizard with OSL and reference materials
- permittivity validation with confidence scoring
- reference-material comparison and material matching
- Touchstone and CSV import
- LiteVNA USB serial acquisition
- plugin-based permittivity transforms
- inverse-modelling engine with uncertainty and sensitivity tooling
- full-wave simulation registry, caching, and comparison workflows
- SQLite-backed experiment archive
- FastAPI service layer
- MkDocs documentation site and browser demo

## What LitePerm Can Do

### Permittivity Measurement Workflow

- Start from a guided Home page
- Connect LiteVNA and configure the sweep
- Run a full calibration wizard
- Select a sensor family and geometry profile
- Capture or import the material measurement
- Calculate complex permittivity as the primary output
- Validate the result and compare against reference materials
- Save the result into Research Mode

### Basic and Advanced Modes

- `Basic Mode` for technicians, students, and routine measurement workflows
- `Advanced Mode` for RF engineers, sensor developers, and modelling work
- Basic Mode keeps the interface focused on frequency, `epsilon'`, `epsilon''`, loss tangent, conductivity, and confidence
- Advanced Mode exposes S11, Smith chart, impedance, admittance, inverse controls, and solver tools

### Measurement and Acquisition

- Import Touchstone `.s1p` files
- Import LiteVNA CSV exports
- Connect to LiteVNA devices over USB serial
- Discover COM ports automatically
- Capture live sweeps into the analysis workspace
- Save measured sweeps into research experiments

### Dielectric Spectroscopy

- Compute complex permittivity across frequency
- Plot `epsilon'` and `epsilon''`
- Plot loss tangent
- Plot conductivity
- Plot Nyquist responses
- Export dielectric spectra to CSV
- Validate measurement plausibility
- Compare measured spectra with built-in reference materials
- Identify closest materials using nearest-neighbour style matching

### RF and Network Analysis

- Plot S11 magnitude
- Plot S11 phase
- Display Smith charts
- Convert reflection coefficient to impedance
- Convert reflection coefficient to admittance
- Compare measured and predicted responses

### Transformation Models

Built-in modelling plugins:

- Stuchly
- Marsland
- Komarov

The plugin architecture is designed so new transform methods can be added without rewriting the app.

### Inverse Electromagnetic Modelling

- Patch antenna forward model
- Open-ended coax probe forward model
- Microstrip resonator forward model
- Generic resonator forward model
- Least-squares inverse solver
- Differential evolution solver
- Particle swarm solver
- Bayesian-style search solver
- MCMC solver
- uncertainty estimation
- sensitivity analysis
- parameter sweeps
- digital twin updates

### Full-Wave Simulation

Phase 4 adds a modular solver integration layer under `liteperm/solvers`.

Current support includes:

- `SimulationJob` model
- `SimulationResult` model
- solver registry
- environment validation
- openEMS adapter scaffold
- Meep adapter scaffold
- cached simulation reuse
- measured versus simulated S11 comparison
- `FullWaveForwardModel` for inverse-modelling workflows

LitePerm is intentionally not locked to one external solver. The architecture is prepared for future openEMS, Meep, HFSS, CST, and COMSOL expansion.

### Research and Data Management

- Research Mode metadata capture
- experiment storage in SQLite
- project-based archive folders under `Projects/`
- calibration profile storage
- geometry profile storage
- experiment duplication, export, and deletion
- material database
- report and archive foundations

### API and Automation

- FastAPI application
- REST endpoints for experiments, materials, calibrations, geometries, sweeps, and plugins
- AI-preparation modules for future dataset building and feature extraction

## Dashboard Overview

The Streamlit dashboard now follows a measurement-first structure:

1. `Home`
   Start from the instrument landing page and choose the next step in the measurement workflow.
2. `Connect LiteVNA`
   Detect the device, connect, test communication, and configure the sweep.
3. `Calibration Wizard`
   Capture or import Open, Short, Load, and reference materials before saving the calibration.
4. `Sensor Setup`
   Choose Open Ended Coax Probe, Patch Sensor, Microstrip Resonator, or Custom Sensor and edit the geometry profile.
5. `Measure Material`
   Capture the material measurement from LiteVNA or import a saved file, then calculate permittivity.
6. `Permittivity Results`
   Review `epsilon'`, `epsilon''`, conductivity, loss tangent, confidence, and reference-material comparisons.
7. `Research Mode`
   Save the experiment, search archived experiments, reopen previous measurements, and export projects.
8. `Advanced Tools`
   Access RF response plots, live capture, calibration/profile management, plugin inspection, full-wave simulation, inverse modelling, and the material database.

## Supported Use Cases

LitePerm is suitable for:

- dielectric spectroscopy research
- RF material characterisation
- patch antenna sensors
- open-ended coaxial probe measurements
- microstrip resonator studies
- moisture sensing
- chemical sensing
- biomedical sensing
- implant sensor research preparation
- simulation-assisted sensor development

## Supported Sensor Families

- Open-ended coaxial probe
- Patch antenna
- Microstrip resonator
- Generic resonator
- Future CSRR and metamaterial structures
- Future implant and passive wireless sensors

## Installation

LitePerm supports:

- Windows 11
- Linux
- WSL2

### Quick Start

```powershell
git clone https://github.com/DionCroft/LitePerm.git
cd LitePerm
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install -r requirements.txt
streamlit run app.py
```

The dashboard is then available at:

```text
http://localhost:8501
```

### Recommended First Measurement

For the cleanest first result:

1. Open `Connect LiteVNA`
2. Complete `Calibration Wizard`
3. Open `Sensor Setup`
4. Open `Measure Material`
5. Press `Calculate Permittivity`
6. Review `Permittivity Results`
7. Save the experiment in `Research Mode`

### Optional API

```powershell
uvicorn liteperm.api.app:create_api_app --factory
```

FastAPI docs:

```text
http://localhost:8000/docs
```

## Documentation

Project website:

- GitHub Pages portal: `https://dioncroft.github.io/LitePerm/`
- Browser demo: `https://dioncroft.github.io/LitePerm/web_demo/`

Recommended starting points:

- [Getting Started](docs/getting_started.md)
- [Permittivity Measurement Guide](docs/permittivity_measurement_guide.md)
- [Calibration Workflow](docs/calibration_workflow.md)
- [Probe Setup Guide](docs/probe_setup_guide.md)
- [Reference Materials Guide](docs/reference_materials_guide.md)
- [Measurement Validation](docs/measurement_validation.md)
- [Quick Install (5 Minutes)](docs/quick_install_5_minutes.md)
- [First LiteVNA Measurement Tutorial](docs/first_litevna_measurement_tutorial.md)
- [Windows 11 Installation Guide](docs/installation_windows_11.md)
- [User Manual](docs/user_manual.md)

Core workflow guides:

- [LiteVNA Setup](docs/litevna_setup.md)
- [Calibration Guide](docs/calibration_guide.md)
- [Patch Antenna Guide](docs/patch_antenna_guide.md)
- [OECP Guide](docs/oecp_guide.md)
- [Inverse Modelling Guide](docs/inverse_modelling_guide.md)
- [Full-Wave Solver Guide](docs/full_wave_solver_guide.md)
- [Simulation Workflow](docs/simulation_workflow.md)
- [Research Mode Guide](docs/research_mode_guide.md)

Solver setup:

- [openEMS Setup Guide](docs/openems_setup_guide.md)
- [Meep Setup Guide](docs/meep_setup_guide.md)

## Repository Structure

```text
LitePerm/
├── app.py
├── docs/
├── examples/
├── liteperm/
│   ├── acquisition/
│   ├── ai/
│   ├── calibration/
│   ├── database/
│   ├── devices/
│   ├── geometry/
│   ├── inverse/
│   ├── permittivity/
│   ├── plugins/
│   ├── sensors/
│   ├── solvers/
│   ├── synthetic/
│   ├── transform/
│   ├── utils/
│   └── visualisation/
└── tests/
```

## Validation

Typical local validation commands:

```powershell
.\.venv\Scripts\python.exe -c "import app; print('app-import-ok')"
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m mkdocs build --strict
```

## Roadmap Direction

LitePerm now prioritises:

- permittivity measurement accuracy
- calibration quality
- reference-material comparison
- material characterisation
- sensor development
- research validation

Advanced modelling, inverse workflows, and full-wave solvers remain important, but they now support the central measurement mission rather than competing with it.

## License

MIT License.
