# Simulation Workflow

This page shows the intended LitePerm full-wave workflow from sensor profile to measured-versus-simulated comparison.

## 1. Create or Load a Sensor Profile

Open `Sensor Geometry` and make sure the active geometry matches the sensor you want to simulate.

Typical examples:

- `patch_antenna`
- `open_ended_coax_probe`
- `microstrip_resonator`
- `generic_resonator`

## 2. Define the Material Stack

Open the `Full-Wave Simulation` tab and edit the material stack.

Typical layers may include:

- air
- protective layer
- material under test
- substrate
- ground plane

## 3. Choose a Solver

LitePerm Phase 4 currently exposes:

- `openems`
- `meep`
- placeholder entries for `hfss`, `cst`, and `comsol`

If a solver is missing, LitePerm will show setup guidance instead of crashing.

## 4. Configure the Sweep

Choose:

- start frequency
- stop frequency
- number of points
- mesh quality
- project name

LitePerm generates a cache key from the geometry, stack, sweep, and solver settings so repeated runs can be reused safely.

## 5. Run or Reuse the Simulation

Use:

- `Reuse cache` when you want faster reruns
- `Force rerun` when geometry or solver settings changed and you want fresh exported outputs

The exported files are stored under:

```text
Projects/<ProjectName>/simulations/<CacheKey>/
```

## 6. Inspect the Results

LitePerm displays:

- simulated S11 magnitude
- simulated S11 phase
- Smith chart
- impedance
- admittance

If exported files are present, you can also download:

- Touchstone `.s1p`
- CSV

## 7. Compare Measured and Simulated Responses

If a measured LiteVNA response is already loaded, LitePerm can display:

- magnitude overlay
- phase overlay
- Smith comparison
- residual error
- scalar comparison metrics such as RMSE

## 8. Use the Result in Inverse Modelling

Open `Inverse Modelling` and choose `Full Wave` as the forward model when you want the inverse engine to reuse:

- the analytical backend
- cached full-wave results
- future solver-backed forward responses

The recommended workflow is still to start analytically, then move to cached or solver-backed forward responses only when higher fidelity is worth the extra cost.

## 9. Archive the Work

Once you have a useful measured or simulated result:

1. Save the experiment in `Research Mode`.
2. Keep the associated geometry and calibration profiles.
3. Preserve the simulation cache directory for reproducibility.

## Example Job Files

See:

- `examples/simulation_jobs/patch_2p45ghz_openems.yaml`
- `examples/simulation_jobs/microstrip_resonator_demo.yaml`
- `examples/simulation_jobs/oecp_placeholder.yaml`
