# Meep Setup Guide

LitePerm includes a Meep adapter scaffold so future resonator and research workflows can grow into full-wave FDTD studies without redesigning the rest of the application.

## Current LitePerm Status

The Meep adapter currently provides:

- environment detection
- registry visibility in the dashboard
- placeholder project export
- documented setup pathway

Full end-to-end Meep execution is not implemented in this LitePerm release.

## Recommended Installation Path

The Meep documentation recommends Conda packages for most users on Linux and macOS.

Typical example:

```bash
conda create -n mp -c conda-forge pymeep
conda activate mp
python -c "import meep as mp; print(mp.__version__)"
```

## Windows 11

The Meep documentation states that native Windows installation is currently unsupported and recommends using Ubuntu through WSL2 instead.

If you want to prepare for future LitePerm Meep workflows on Windows:

1. Install WSL2 with Ubuntu.
2. Install Conda or Miniforge inside WSL2.
3. Install `pymeep` in that Linux environment.
4. Keep notes about the Meep environment location for future LitePerm integration work.

## Ubuntu / Linux

For Linux users, the recommended path is:

1. Install Miniforge or Miniconda.
2. Create a dedicated environment:

```bash
conda create -n mp -c conda-forge pymeep
conda activate mp
python -c "import meep as mp; print(mp.__version__)"
```

3. If you want Jupyter-based plotting, add `jupyter` to the environment.

## macOS

The Meep documentation recommends Conda for most macOS users as well.

If you need a source build later, keep that work in a separate solver environment rather than mixing it into your main LitePerm environment.

## What LitePerm Checks

The current LitePerm scaffold checks for a `meep` executable on `PATH`.

That means:

- a Python-only `import meep` install may still appear as missing in LitePerm
- this is acceptable for Phase 4 because the adapter is still a scaffold
- future releases can expand detection to cover Python-only installs

## Troubleshooting

### LitePerm says Meep is missing but `import meep` works

The current adapter checks for the command-line executable, not just the Python package.

### Native Windows install

Use WSL2 instead. That matches the current Meep documentation and will be the most reliable path for early LitePerm Meep experiments.

## References

- Meep installation docs: https://meep.readthedocs.io/en/latest/Installation/
