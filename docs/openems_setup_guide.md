# openEMS Setup Guide

LitePerm currently uses `openEMS` as the primary Phase 4 full-wave solver target.

This page focuses on practical setup for LitePerm users on Windows, WSL2, and Linux.

## Current LitePerm Expectations

The LitePerm adapter currently checks for:

- `openEMS`
- `openEMS.exe`

If LitePerm cannot find one of these on your `PATH`, the dashboard will report the solver as missing and link back to this guide.

## Windows 11

The openEMS documentation provides a Windows 64-bit build and describes unzipping it to a folder such as `C:/openEMS` or `C:/opt/openEMS`.

Recommended LitePerm workflow:

1. Download the latest 64-bit Windows build from the openEMS project.
2. Extract it to a simple path such as `C:\opt\openEMS`.
3. Add the openEMS binary folder to your `PATH`.
4. Restart PowerShell.
5. Verify detection:

```powershell
Get-Command openEMS.exe
```

If you want the Python interface as well, the openEMS Python install page documents wheel-based installation from the `python` subdirectory and the `OPENEMS_INSTALL_PATH` environment variable.

Example:

```powershell
setx OPENEMS_INSTALL_PATH C:\opt\openEMS
```

## WSL2

WSL2 is often the cleanest path when you want a Linux-style build environment on Windows.

Recommended workflow:

1. Install Ubuntu in WSL2.
2. Follow the Linux build steps below inside the Ubuntu shell.
3. Store LitePerm projects in a folder that both Windows and WSL2 can access.
4. Run LitePerm from Windows or WSL2 depending on your preferred workflow.

## Ubuntu / Linux

The openEMS documentation lists a source-build workflow based on:

```bash
sudo apt-get install build-essential cmake git libhdf5-dev libboost-all-dev libcgal-dev libtinyxml-dev qtbase5-dev
git clone --recursive https://github.com/thliebig/openEMS-Project.git
cd openEMS-Project
./update_openEMS.sh ~/opt/openEMS
```

For the Python interface, the project documentation also notes Python packages such as:

```bash
pip install numpy matplotlib cython h5py
```

After installation, add the solver binaries to your shell path if needed.

## Verification

LitePerm only needs to detect the solver executable for Phase 4 adapter status.

Suggested checks:

```powershell
openEMS --help
```

or on Linux:

```bash
which openEMS
openEMS --help
```

If the command is missing, fix `PATH` first and then restart LitePerm.

## What LitePerm Does Today

In this release, the adapter focuses on:

- environment checking
- simulation-job export
- cache reuse
- a clean pathway for patch-style solver workflows

That means Phase 4 is ready for structured simulation workflow development, even though deeper solver automation will continue to improve in future releases.

## Troubleshooting

### LitePerm still says openEMS is missing

- confirm `openEMS` or `openEMS.exe` is on `PATH`
- open a new terminal after changing environment variables
- verify you are launching LitePerm from the same environment where openEMS is available

### Python interface import fails

- re-check the wheel or build instructions from the openEMS Python interface page
- confirm `OPENEMS_INSTALL_PATH` points at the extracted or installed openEMS folder
- make sure the Python version you use for LitePerm matches the wheel you installed

### WSL2 build succeeds but Windows LitePerm does not detect openEMS

- Windows and WSL2 do not share shell `PATH` values automatically
- either run LitePerm inside WSL2 or install a native Windows openEMS build as well

## References

- openEMS install docs: https://docs.openems.de/install.html
- openEMS Python interface docs: https://docs.openems.de/python/install.html
