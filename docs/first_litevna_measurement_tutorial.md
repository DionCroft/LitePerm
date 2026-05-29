# First LiteVNA Measurement Tutorial

This tutorial answers the question most new users ask first:

> How do I get from my LiteVNA to a permittivity plot?

## Goal

By the end of this tutorial you will:

1. export S11 from a LiteVNA
2. import the file into LitePerm
3. view the Smith chart
4. view the dielectric spectrum
5. save the experiment

Estimated time:

`10-15 minutes`

## Before You Start

You need:

- LitePerm installed and running
- a LiteVNA measurement exported as `.s1p` or CSV
- or one of the bundled example files

If LitePerm is not installed yet, use [Quick Install (5 Minutes)](quick_install_5_minutes.md) or the full [Windows 11 Installation Guide](installation_windows_11.md).

## Step 1 - Export the Measurement

From your LiteVNA workflow, export S11 as either:

- Touchstone `.s1p`
- CSV

If you do not have a real sweep yet, use:

- `examples/sample_touchstone.s1p`
- `examples/sample_litevna.csv`

## Step 2 - Open LitePerm

Start the dashboard:

```powershell
streamlit run app.py
```

Open the local URL shown in PowerShell.

## Step 3 - Import the File

In `Raw Measurement`:

1. Click the file uploader
2. Select your `.s1p` or CSV file
3. Wait for the plots to appear

You should now see:

- S11 magnitude
- S11 phase
- Smith chart

## Step 4 - Confirm Geometry

Open `Sensor Geometry`.

For a first OECP-style measurement, leave the default `open_ended_coax_probe` geometry unless you already know your sensor dimensions.

## Step 5 - View Permittivity

Open `Material Properties`.

You should now see:

- epsilon'
- epsilon''
- loss tangent
- conductivity

If these appear, the core pipeline is working:

```text
S11 -> Impedance -> Admittance -> Permittivity
```

## Step 6 - Save the Experiment

Open `Research Mode`.

Fill in:

- Experiment Name
- Researcher
- Project Name
- Material Under Test

Then click:

`Save Experiment`

## Step 7 - Reopen It

Open `Experiment Explorer`.

Select the saved experiment and reload it into the workspace. This confirms the archive and database workflow is functioning.

## Optional Next Steps

Once your first measurement works, try:

- [Calibration Guide](calibration_guide.md)
- [OECP Sensors](oecp_guide.md)
- [Inverse Modelling Guide](inverse_modelling_guide.md)
- [LiteVNA Setup](litevna_setup.md)

## Common First-Tutorial Problems

### The file imports but no useful plots appear

Check that:

- the file really contains S11 data
- the sweep has more than one sample point
- the file format is `.s1p` or a LitePerm-compatible CSV

### The Smith chart loads but permittivity does not

Make sure you opened the `Material Properties` tab after importing the file.

### I want live capture instead of file import

Use the `Live Measurement` tab and follow [LiteVNA Setup](litevna_setup.md).
