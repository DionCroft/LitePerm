# LitePerm Web Demo

The LitePerm Web Demo runs entirely in your browser. It does not require Python, Streamlit, or a backend service.

## What It Can Do

- upload Touchstone `.s1p` files
- upload CSV exports
- plot S11 magnitude
- plot S11 phase
- render a Smith chart view
- compute a lightweight permittivity visualisation

## Important Note

The permittivity plot on this page is an educational, browser-side approximation intended for quick investigation and teaching. For research-grade calibration, experiment storage, and inverse modelling, use the full Python application.

<div id="liteperm-demo-root" class="demo-shell">
  <div class="demo-control-grid">
    <label>
      <strong>Touchstone or CSV file</strong>
      <input id="liteperm-demo-file" type="file" accept=".s1p,.csv,text/plain,text/csv" />
    </label>
    <label>
      <strong>Reference impedance Z0 (Ohm)</strong>
      <input id="liteperm-demo-z0" type="number" value="50" step="1" />
    </label>
    <label>
      <strong>Reference capacitance C0 (F)</strong>
      <input id="liteperm-demo-c0" type="number" value="1e-12" step="1e-13" />
    </label>
  </div>
  <div class="demo-button-row">
    <button id="liteperm-demo-load-sample" type="button">Load built-in sample</button>
    <button id="liteperm-demo-clear" type="button" class="secondary">Clear</button>
  </div>
  <p class="demo-help">
    The demo uses an OECP-style approximation to turn admittance into epsilon' and epsilon'' for browser-side visualisation.
  </p>
  <div id="liteperm-demo-status" class="demo-status"></div>
  <div id="liteperm-demo-metrics" class="demo-metrics"></div>
  <div class="demo-plot-grid">
    <div id="liteperm-demo-magnitude" class="demo-plot"></div>
    <div id="liteperm-demo-phase" class="demo-plot"></div>
    <div id="liteperm-demo-smith" class="demo-plot"></div>
    <div id="liteperm-demo-permittivity" class="demo-plot"></div>
  </div>
</div>

## Good Uses for the Demo

- quick previews during teaching or presentations
- checking whether a Touchstone export looks reasonable
- showing colleagues the LitePerm workflow without local installation
- embedding a low-friction example in documentation or workshops
