# LitePerm

<div class="lp-hero">
  <div>
    <p class="lp-eyebrow">Open-source permittivity measurement platform</p>
    <h1>Connect LiteVNA, calibrate the sensor, measure the material, and calculate epsilon' and epsilon''.</h1>
    <p>
      LitePerm turns LiteVNA S11 measurements into guided dielectric spectroscopy workflows
      with calibration, probe-centric setup, permittivity validation, material comparison,
      experiment storage, and advanced modelling when you need it.
    </p>
    <div class="lp-button-row">
      <a class="md-button md-button--primary" href="getting_started.md">Get Started</a>
      <a class="md-button" href="permittivity_measurement_guide.md">Permittivity Measurement Guide</a>
      <a class="md-button" href="calibration_workflow.md">Calibration Workflow</a>
      <a class="md-button" href="quick_install_5_minutes.md">Quick Install</a>
      <a class="md-button" href="first_litevna_measurement_tutorial.md">First Measurement Tutorial</a>
      <a class="md-button" href="user_manual.md">User Manual</a>
      <a class="md-button" href="https://github.com/DionCroft/LitePerm">View on GitHub</a>
    </div>
  </div>
  <div class="lp-kpi-grid">
    <div class="lp-kpi-card"><strong>Phase 5</strong><span>Permittivity-first workflow with Basic and Advanced measurement modes</span></div>
    <div class="lp-kpi-card"><strong>LiteVNA-ready</strong><span>USB serial capture, Touchstone import, CSV import</span></div>
    <div class="lp-kpi-card"><strong>Validation aware</strong><span>Confidence scoring, reference comparison, material matching</span></div>
    <div class="lp-kpi-card"><strong>Research archive</strong><span>SQLite experiments, project folders, YAML profiles, reports</span></div>
  </div>
</div>

## What LitePerm Is For

<div class="grid cards" markdown>

-   :material-flask-outline: **Permittivity measurement**

    Build a guided instrument workflow around calibration, probe setup, measurement, validation, and material comparison.

-   :material-chart-bell-curve-cumulative: **Dielectric spectroscopy**

    Convert measured S11 into conductivity, loss tangent, and complex permittivity across frequency.

-   :material-function-variant: **Inverse electromagnetic modelling**

    Move into Advanced Mode when you need forward models, inverse solvers, uncertainty analysis, or full-wave support.

-   :material-hospital-box-outline: **Biomedical and materials research**

    Support implant sensors, liquids, polymers, moisture studies, and material-characterisation workflows.

</div>

## Architecture

![LitePerm architecture diagram](images/architecture-diagram.svg)

The core LitePerm measurement pipeline is intentionally modular:

1. Connect LiteVNA or import a sweep
2. Run the calibration wizard
3. Select the sensor geometry
4. Calculate permittivity
5. Validate and compare the result
6. Save the experiment

## Screenshots

<div class="lp-gallery">
  <div class="lp-gallery-card">
    <img src="images/dashboard-overview.svg" alt="LitePerm dashboard overview placeholder" />
    <div><strong>Dashboard</strong><br />Upload, visualise, and route measurements into the analysis workflow.</div>
  </div>
  <div class="lp-gallery-card">
    <img src="images/smith-chart-view.svg" alt="Smith chart placeholder" />
    <div><strong>Smith Chart</strong><br />Inspect reflection trajectories and compare measured and predicted responses.</div>
  </div>
  <div class="lp-gallery-card">
    <img src="images/permittivity-results.svg" alt="Permittivity results placeholder" />
    <div><strong>Permittivity Results</strong><br />Explore epsilon', epsilon'', conductivity, and loss tangent across frequency.</div>
  </div>
  <div class="lp-gallery-card">
    <img src="images/inverse-modelling-view.svg" alt="Inverse modelling placeholder" />
    <div><strong>Inverse Modelling</strong><br />Estimate material properties and inspect convergence, residuals, and confidence intervals.</div>
  </div>
  <div class="lp-gallery-card">
    <img src="images/full-wave-simulation-view.svg" alt="Full-wave simulation placeholder" />
    <div><strong>Full-Wave Simulation</strong><br />Review solver status, configure a simulation job, and compare measured versus simulated S11.</div>
  </div>
  <div class="lp-gallery-card">
    <img src="images/research-mode-view.svg" alt="Research mode placeholder" />
    <div><strong>Research Mode</strong><br />Capture metadata, save structured experiments, and generate long-term archives.</div>
  </div>
  <div class="lp-gallery-card">
    <img src="images/experiment-explorer-view.svg" alt="Experiment explorer placeholder" />
    <div><strong>Experiment Explorer</strong><br />Search, duplicate, export, and reopen previous experiments.</div>
  </div>
  <div class="lp-gallery-card">
    <img src="images/live-acquisition-view.svg" alt="Live acquisition placeholder" />
    <div><strong>Live LiteVNA Acquisition</strong><br />Configure sweep capture and push live measurements into the analysis stack.</div>
  </div>
</div>

## Quick Start

```bash
git clone https://github.com/DionCroft/LitePerm.git
cd LitePerm
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

If you want the fastest path to a first result, follow the [Permittivity Measurement Guide](permittivity_measurement_guide.md) and the [Quick Start guide](QuickStart.md).

## Project Snapshot

| Area | Current capability |
| --- | --- |
| Import | Touchstone `.s1p`, CSV, LiteVNA live acquisition |
| Measurement | Calibration wizard, sensor setup, permittivity validation, reference comparison |
| Analysis | Permittivity, conductivity, loss tangent, plus advanced RF views when needed |
| Modelling | Stuchly-style transforms, forward models, inverse solvers |
| Simulation | openEMS adapter path, Meep scaffold, simulation cache, measured-vs-simulated overlays |
| Storage | SQLite experiment database plus project archive folders |
| Web | GitHub Pages portal and browser-only static demo |

## Roadmap

<div class="lp-callout">
  LitePerm now includes a modular full-wave solver layer on top of the existing measurement, inverse-modelling, and research stack. The next major engineering milestones are deeper solver automation, real-time streaming, and AI-assisted inverse workflows.
</div>

Explore the full [Roadmap](roadmap.md), [Release Notes](release_notes.md), and [Downloads](downloads.md).
