# Live Measurement Guide

LitePerm supports direct capture pipelines through device adapters that share a common interface.

## Workflow

1. Open `Live Measurement`.
2. Select a device backend.
3. Choose a detected COM port or provide a manual override.
4. Connect and test the device.
5. Configure start frequency, stop frequency, point count, output power, and sweep speed.
6. Start the sweep and monitor magnitude, phase, Smith chart, and permittivity updates.
7. Save the latest sweep into the analysis workspace or Research Mode.

## Current Backends

- `LiteVNADevice`
- `FutureDevice` simulated backend

## Notes

- The simulated backend is useful when hardware is unavailable.
- The live pipeline routes captures through the current geometry profile and selected transform workflow.
- The LiteVNA backend uses the documented USB CDC serial protocol and captures raw S11 data for processing in LitePerm.
