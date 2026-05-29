# Full-Wave Solver Guide

LitePerm Phase 4 adds a modular full-wave solver layer so measured LiteVNA data can be compared against simulation-backed forward responses.

## Why Full-Wave Solvers Matter

Analytical models are fast and ideal for routine inverse fitting, parameter sweeps, and day-to-day research iteration.

Full-wave solvers are useful when:

- fringing fields dominate the sensor response
- the sensing stack is strongly multilayered
- geometry is too complex for a simple resonator approximation
- you need a higher-fidelity forward response for publication or design validation

## LitePerm Architecture

LitePerm keeps solver coupling modular:

```text
Sensor Geometry
      ->
Material Stack
      ->
Simulation Job
      ->
Solver Adapter
      ->
S-Parameter Result
      ->
Forward Model / Inverse Model / Visualisation
```

This means the same application can grow from lightweight analytical studies into simulation-assisted workflows without redesigning the rest of the platform.

## What Phase 4 Includes

- `liteperm/solvers/` package for job models, result models, adapters, registry, exporters, cache helpers, and validation
- `SimulationJob` for reproducible solver inputs
- `SimulationResult` for solver outputs that plug back into LitePerm plots and inverse modelling
- `FullWaveForwardModel` for analytical, cached, and solver-backed forward workflows
- simulation caching under `Projects/<ProjectName>/simulations/`
- a new `Full-Wave Simulation` dashboard tab

## Current Solver Status

### openEMS

- environment detection is implemented
- project and geometry export is implemented
- patch-style workflow export is implemented first
- cached-result reuse is implemented
- the adapter is intentionally conservative and documents the exported workflow clearly

### Meep

- environment detection is implemented
- adapter scaffold is implemented
- placeholder project export is implemented
- full end-to-end execution is not implemented in this LitePerm release

## Full-Wave vs Analytical Models

Use analytical forward models when:

- you want fast inverse optimisation
- you are screening many candidate materials
- you are still tuning geometry and calibration

Use full-wave simulation when:

- you need stronger geometry fidelity
- multilayer effects matter
- you want measured-versus-simulated overlay plots
- you want to prepare higher-confidence publication figures

## Inverse-Modelling Integration

The `FullWaveForwardModel` supports four operating modes:

- `analytical`: use the current LitePerm analytical baseline
- `openems`: run or reuse an openEMS-backed solver job
- `cached`: reuse a previously exported simulation without rerunning the solver
- `surrogate`: reserved for future AI-assisted surrogate modelling

The default recommendation is still:

1. Start with the analytical backend.
2. Save a stable geometry and layer stack.
3. Run or cache a full-wave job.
4. Switch to cached or solver-backed forward responses only when you need the extra fidelity.

## Outputs

Full-wave results feed back into the existing LitePerm stack as:

- simulated S11 magnitude and phase
- Smith chart traces
- impedance and admittance plots
- measured versus simulated overlays
- residual error plots
- inverse-model forward responses

## Related Pages

- [Simulation Workflow](simulation_workflow.md)
- [openEMS Setup Guide](openems_setup_guide.md)
- [Meep Setup Guide](meep_setup_guide.md)
- [Inverse Modelling Guide](inverse_modelling_guide.md)
