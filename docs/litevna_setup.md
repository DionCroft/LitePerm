# LiteVNA Setup

LitePerm supports two practical LiteVNA workflows:

1. **File import** using Touchstone or CSV exports
2. **Direct USB serial capture** through the `Live Measurement` tab

## Recommended First Session

Start with file import even if you eventually want live capture. It lets you verify the software stack before introducing hardware or serial-port variables.

## File Export Workflow

1. Measure `S11` on the LiteVNA or companion desktop software.
2. Export the sweep as `.s1p` or CSV.
3. Open `Raw Measurement` in LitePerm.
4. Import the file and confirm:
   - S11 magnitude
   - phase
   - Smith chart
5. Continue into `Material Properties` or `Inverse Modelling`.

## Direct USB Serial Workflow

1. Connect the LiteVNA to your computer.
2. Open `Live Measurement`.
3. Choose the `LiteVNA USB Serial` backend.
4. Confirm or override the COM port.
5. Click `Test Connection`.
6. Configure sweep limits and points.
7. Start the sweep and save the result into the current workspace.

## Suggested Sweep Baselines

| Use case | Start | Stop | Points |
| --- | ---: | ---: | ---: |
| Quick sanity check | 100 MHz | 2 GHz | 201 |
| OECP dielectric sweep | 100 MHz | 6 GHz | 401 |
| Patch resonator around a known band | sensor-dependent | sensor-dependent | 401 to 801 |
| Browser demo reproduction | 800 MHz | 3.2 GHz | 201 |

## Good Measurement Practice

- Use the same sweep settings for open, short, load, and DUT
- Save calibration and geometry profiles early
- Record temperature and humidity for sensitive material studies
- Export raw data even if you also save a LitePerm experiment

## Troubleshooting

### Device connects but sweep fails

- reduce the point count
- confirm no other serial client is open
- try the simulated backend to separate software issues from hardware issues

### Device is not listed

- verify the USB cable supports data
- confirm the operating system sees the COM port
- enter the port manually if discovery fails

### Want browser-based hardware access?

See [Browser Connectivity](BrowserConnectivity.md). As of May 29, 2026, browser-side serial support should be treated as experimental and Chromium-first.
