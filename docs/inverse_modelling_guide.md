# Inverse Modelling Guide

LitePerm Phase 3 adds a full inverse electromagnetic modelling workflow on top of the existing dielectric-spectrum pipeline.

## What it does

The inverse engine estimates unknown material properties by minimising the mismatch between:

- measured `S11`
- predicted `S11` from a forward model

The current Streamlit workflow supports:

- forward-model selection
- solver selection
- error-metric selection
- multilayer stack editing
- parameter estimation
- uncertainty analysis
- sensitivity analysis
- parameter sweeps
- digital twin updates

## Current forward models

- Patch antenna
- Open-ended coax probe
- Microstrip resonator
- Generic resonator

These are research-grade simplified models intended for rapid iteration and benchmarking. The architecture is prepared for future links to HFSS, CST, COMSOL, openEMS, and Meep.

## Recommended workflow

1. Import or capture a measurement in LitePerm.
2. Load or define the sensor geometry.
3. Open the `Inverse Modelling` tab.
4. Choose the closest forward model for the sensor.
5. Edit the layer stack so it matches the experiment.
6. Select the unknown parameters to estimate.
7. Choose a solver and error metric.
8. Run the inverse estimation.
9. Inspect measured vs predicted S11, residuals, confidence intervals, and sensitivity ranking.
10. Save the experiment to preserve the inverse result and digital twin snapshot.

## Solvers

- Least Squares: fastest local solver when the initial guess is already reasonable.
- Differential Evolution: global search with stronger robustness and higher cost.
- Particle Swarm: good exploratory search for coupled parameters.
- Bayesian Optimisation: lightweight surrogate-guided search.
- MCMC: exploratory posterior-style sampling with interval outputs.

## Error metrics

- `weighted_error`
- `complex_error`
- `magnitude_error`
- `phase_error`
- `multi_objective_error`
- `rmse`
- `mse`
- `mae`

## Outputs

LitePerm currently exposes:

- estimated parameter set
- predicted resonant frequency
- measured vs predicted S11
- Smith chart comparison
- residual plot
- convergence plot
- confidence interval plot
- sensitivity heatmap
- tornado plot
- 3D parameter-space explorer
- layer-stack viewer

## Notes

- Inverse results are model dependent. Choose the forward model that best matches the sensor physics.
- The current models are intentionally lightweight and should be treated as research baselines, not full-wave replacements.
- For publication-quality studies, validate the parameter estimates against reference materials, synthetic benchmarks, or external EM solvers.
