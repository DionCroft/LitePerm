# Inverse Modelling Guide

LitePerm Phase 3 turned the project from a measurement viewer into an inverse electromagnetic research platform.

## What You Can Estimate

- complex permittivity
- conductivity
- loss tangent
- material thickness
- multilayer dielectric properties

## Supported Forward Models

- patch antenna
- open-ended coax probe
- microstrip resonator
- generic resonator

## Supported Solver Families

- least squares
- differential evolution
- particle swarm
- Bayesian-style search
- MCMC

## Recommended Workflow

1. Import or capture a measurement.
2. Load the closest geometry profile.
3. Open `Inverse Modelling`.
4. Choose the forward model.
5. Edit the layer stack.
6. Select the parameters to estimate.
7. Choose a solver and error metric.
8. Run the estimation.
9. Inspect residuals, convergence, confidence intervals, and sensitivity plots.
10. Save the experiment so the inverse result and digital twin are archived together.
