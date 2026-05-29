# Getting Started

LitePerm serves three main kinds of users:

| If you want to... | Start here |
| --- | --- |
| Install LitePerm for the first time | [Installation Guide](installation_guide.md) |
| Get the dashboard running as fast as possible | [Quick Install (5 Minutes)](quick_install_5_minutes.md) |
| Get from zero to a saved experiment in one session | [Quick Start](QuickStart.md) |
| Go from LiteVNA export to a permittivity plot | [First LiteVNA Measurement Tutorial](first_litevna_measurement_tutorial.md) |
| Learn the whole system end to end | [User Manual](user_manual.md) |
| Connect a LiteVNA and capture live data | [LiteVNA Setup](litevna_setup.md) |
| Explore the project before installing Python | [Web Demo](web_demo.md) |
| Learn the full measurement workflow | [Permittivity Measurement Guide](permittivity_measurement_guide.md) |

## Choose Your First Session

### Basic measurement workflow

Use this if your goal is to measure permittivity as quickly and clearly as possible.

1. Install LitePerm locally.
2. Launch Streamlit.
3. Open `Connect LiteVNA` or import `examples/sample_touchstone.s1p`.
4. Complete the `Calibration Wizard`.
5. Open `Sensor Setup`.
6. Open `Measure Material` and calculate permittivity.
7. Review `Permittivity Results`.
8. Save the result in `Research Mode`.

### Instrument-first workflow

Use this if you want direct USB capture from a LiteVNA-class device.

1. Install LitePerm and USB serial dependencies.
2. Connect your device and identify the COM port.
3. Open `Connect LiteVNA`.
4. Configure the sweep and test the connection.
5. Run `Calibration Wizard`.
6. Open `Measure Material`.
7. Review `Permittivity Results`.

### Modelling-first workflow

Use this if you want to estimate unknown material properties.

1. Import or capture a measurement.
2. Complete the calibration and sensor setup workflow first.
3. Switch to `Advanced Mode`.
4. Open `Advanced Tools`.
5. Use `Inverse` or `Full-Wave`.
6. Define the layer stack.
7. Run an optimiser and inspect the uncertainty outputs.

## What Gets Installed

The main LitePerm application gives you:

- Streamlit dashboard
- FastAPI service
- calibration wizard and geometry profiles
- permittivity validation and reference comparison
- experiment storage
- inverse modelling engine
- browser documentation portal

## What To Keep Open While Learning

- [Installation Guide](installation_guide.md)
- [Permittivity Measurement Guide](permittivity_measurement_guide.md)
- [Calibration Workflow](calibration_workflow.md)
- [Probe Setup Guide](probe_setup_guide.md)
- [Inverse Modelling Guide](inverse_modelling_guide.md)
- [User Manual](user_manual.md)

## Recommended First Goal

For most users, the best first milestone is:

> Import one S11 file, view the Smith chart, calculate permittivity, and save one experiment.

For most new users, a better first goal is:

> Connect LiteVNA, run calibration, measure one material, review the confidence score, and save one experiment.

That path is covered in the [Permittivity Measurement Guide](permittivity_measurement_guide.md) and the [Quick Start guide](QuickStart.md).
