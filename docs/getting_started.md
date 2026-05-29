# Getting Started

LitePerm serves three main kinds of users:

| If you want to... | Start here |
| --- | --- |
| Install LitePerm for the first time | [Installation Guide](installation_guide.md) |
| Get from zero to a saved experiment in one session | [Quick Start](QuickStart.md) |
| Connect a LiteVNA and capture live data | [LiteVNA Setup](litevna_setup.md) |
| Explore the project before installing Python | [Web Demo](web_demo.md) |

## Choose Your First Session

### File-first workflow

Use this if you already have a LiteVNA export or a Touchstone file.

1. Install LitePerm locally.
2. Launch Streamlit.
3. Import `examples/sample_touchstone.s1p` or your own file.
4. Open `Material Properties` to inspect dielectric outputs.
5. Save the result in `Research Mode`.

### Instrument-first workflow

Use this if you want direct USB capture from a LiteVNA-class device.

1. Install LitePerm and USB serial dependencies.
2. Connect your device and identify the COM port.
3. Open `Live Measurement`.
4. Configure the sweep and test the connection.
5. Capture, review, and save the result.

### Modelling-first workflow

Use this if you want to estimate unknown material properties.

1. Import or capture a measurement.
2. Load the right geometry profile.
3. Open `Inverse Modelling`.
4. Define the layer stack.
5. Run an optimiser and inspect the uncertainty outputs.

## What Gets Installed

The main LitePerm application gives you:

- Streamlit dashboard
- FastAPI service
- calibration and geometry profiles
- experiment storage
- inverse modelling engine
- browser documentation portal

## What To Keep Open While Learning

- [Installation Guide](installation_guide.md)
- [Calibration Guide](calibration_guide.md)
- [OECP Guide](oecp_guide.md)
- [Inverse Modelling Guide](inverse_modelling_guide.md)

## Recommended First Goal

For most users, the best first milestone is:

> Import one S11 file, view the Smith chart, calculate permittivity, and save one experiment.

That is the exact path covered in the [Quick Start guide](QuickStart.md).
