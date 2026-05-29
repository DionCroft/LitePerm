# Quick Start

This path is designed so a first-time user can get from zero to a saved LitePerm experiment in about 15 minutes.

## Goal

By the end of this guide you will:

1. launch LitePerm
2. import S11 data
3. view permittivity
4. save an experiment

## Step 1: Install and Launch

Follow the [Installation Guide](installation_guide.md), then run:

```bash
streamlit run app.py
```

## Step 2: Load a Sample Dataset

In `Raw Measurement`:

1. Click **Load example dataset**
2. Choose `sample_touchstone.s1p`
3. Confirm the magnitude, phase, and Smith chart appear

## Step 3: Check Geometry

Open `Sensor Geometry` and keep the default `open_ended_coax_probe` profile unless you already have a specific sensor.

## Step 4: View Permittivity

Open `Material Properties`.

You should now see:

- epsilon'
- epsilon''
- loss tangent
- conductivity

## Step 5: Save an Experiment

Open `Research Mode`.

Fill in:

- Experiment Name
- Researcher
- Project Name
- Material Under Test

Click **Save Experiment**.

## Step 6: Reopen It

Open `Experiment Explorer`, choose the saved experiment, and load it back into the workspace.

## Success Checklist

You are finished when all of these are true:

- the app opens without errors
- a dataset imports successfully
- the Smith chart renders
- dielectric plots render
- one experiment is saved and reloads correctly

## Next Steps

- Use your own LiteVNA export
- add calibration standards in [Calibration](calibration_guide.md)
- try the [Inverse Modelling](inverse_modelling_guide.md) tab
- experiment with the [Web Demo](web_demo.md) for teaching or quick previews
