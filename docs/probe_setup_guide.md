# Probe Setup Guide

LitePerm is probe-centric. The selected sensor type shapes the measurement workflow, geometry, modelling options, and how the permittivity result should be interpreted.

## Supported Sensor Types

LitePerm currently supports:

- Open Ended Coax Probe
- Patch Sensor
- Microstrip Resonator
- Custom Sensor

## Open Ended Coax Probe

Use this when the measurement is dominated by the probe aperture at the sensing interface.

Typical geometry fields:

- inner radius
- outer radius
- flange radius
- cable permittivity

Recommended when:

- measuring liquids
- comparing solvents
- performing direct-contact dielectric spectroscopy

## Patch Sensor

Use this when the sensing response is resonance-driven and affected by the material above or within the sensing region.

Typical geometry fields:

- patch length
- patch width
- substrate height
- substrate permittivity
- feed position
- ground dimensions
- sensing region dimensions
- protective layer thickness

Recommended when:

- tracking resonance shift
- characterising thin layers
- studying surface-loaded materials

## Microstrip Resonator

Use this when the sensing structure is a distributed resonator rather than a probe aperture.

Typical geometry fields:

- line length
- line width
- substrate height
- substrate permittivity
- coupling gap
- sensing window length

## Custom Sensor

Use this when you want LitePerm to preserve the workflow while you enter user-defined parameters.

This is useful for:

- experimental fixtures
- early-stage prototypes
- sensor concepts that do not yet have a dedicated LitePerm forward model

## General Setup Advice

- Keep the geometry profile aligned with the physical sensor actually attached to the LiteVNA.
- Save geometry profiles once they are verified.
- Re-check geometry after any probe rebuild or fixture change.
- Re-run calibration after large geometry changes.

## Basic vs Advanced Use

In Basic Mode, sensor setup is mainly about selecting the right probe family and entering trusted dimensions.

In Advanced Mode, the same geometry can also feed:

- inverse modelling
- full-wave simulation
- solver comparison

## Related Guides

- [Permittivity Measurement Guide](permittivity_measurement_guide.md)
- [Calibration Workflow](calibration_workflow.md)
- [Full-Wave Simulation](full_wave_solver_guide.md)
