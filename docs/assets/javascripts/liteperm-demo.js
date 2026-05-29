(function () {
  "use strict";

  function complex(re, im) {
    return { re: re, im: im };
  }

  function cAdd(a, b) {
    return complex(a.re + b.re, a.im + b.im);
  }

  function cSub(a, b) {
    return complex(a.re - b.re, a.im - b.im);
  }

  function cMul(a, b) {
    return complex(a.re * b.re - a.im * b.im, a.re * b.im + a.im * b.re);
  }

  function cScale(a, value) {
    return complex(a.re * value, a.im * value);
  }

  function cDiv(a, b) {
    const denominator = b.re * b.re + b.im * b.im || 1e-18;
    return complex(
      (a.re * b.re + a.im * b.im) / denominator,
      (a.im * b.re - a.re * b.im) / denominator
    );
  }

  function magnitudeDb(value) {
    const magnitude = Math.max(Math.hypot(value.re, value.im), 1e-12);
    return 20 * Math.log10(magnitude);
  }

  function phaseDeg(value) {
    return (Math.atan2(value.im, value.re) * 180) / Math.PI;
  }

  function fromMagnitudeAngle(magnitude, angleDeg) {
    const radians = (angleDeg * Math.PI) / 180;
    return complex(magnitude * Math.cos(radians), magnitude * Math.sin(radians));
  }

  function fromDbAngle(dbValue, angleDeg) {
    return fromMagnitudeAngle(Math.pow(10, dbValue / 20), angleDeg);
  }

  function normalizeText(text) {
    return text.replace(/\r/g, "").trim();
  }

  function parseTouchstone(text) {
    const lines = normalizeText(text).split("\n");
    let frequencyUnit = "ghz";
    let dataFormat = "ri";
    const frequencyMultipliers = {
      hz: 1,
      khz: 1e3,
      mhz: 1e6,
      ghz: 1e9,
    };
    const frequencies = [];
    const s11 = [];

    lines.forEach((line) => {
      const trimmed = line.trim();
      if (!trimmed || trimmed.startsWith("!")) {
        return;
      }
      if (trimmed.startsWith("#")) {
        const header = trimmed.toLowerCase().split(/\s+/);
        if (header.length >= 4) {
          frequencyUnit = header[1] || frequencyUnit;
          dataFormat = header[3] || dataFormat;
        }
        return;
      }
      const parts = trimmed.split(/[\s,]+/).map(Number).filter((value) => !Number.isNaN(value));
      if (parts.length < 3) {
        return;
      }
      frequencies.push(parts[0] * (frequencyMultipliers[frequencyUnit] || 1));
      if (dataFormat === "ma") {
        s11.push(fromMagnitudeAngle(parts[1], parts[2]));
      } else if (dataFormat === "db") {
        s11.push(fromDbAngle(parts[1], parts[2]));
      } else {
        s11.push(complex(parts[1], parts[2]));
      }
    });

    return { frequencyHz: frequencies, s11: s11, source: "Touchstone upload" };
  }

  function parseCsv(text) {
    const lines = normalizeText(text).split("\n");
    if (lines.length < 2) {
      throw new Error("CSV file does not contain enough rows.");
    }
    const headers = lines[0].split(",").map((item) => item.trim().toLowerCase());
    const rows = lines.slice(1).map((line) => line.split(",").map((item) => item.trim()));
    const frequencyIndex =
      headers.indexOf("frequency_hz") >= 0
        ? headers.indexOf("frequency_hz")
        : headers.indexOf("frequency") >= 0
          ? headers.indexOf("frequency")
          : 0;
    const realIndex = headers.indexOf("s11_real");
    const imagIndex = headers.indexOf("s11_imag");
    const dbIndex = headers.indexOf("s11_db");
    const magnitudeIndex = headers.indexOf("s11_magnitude");
    const phaseIndex = headers.indexOf("s11_phase_deg");
    const frequencies = [];
    const s11 = [];

    rows.forEach((columns) => {
      const frequency = Number(columns[frequencyIndex]);
      if (Number.isNaN(frequency)) {
        return;
      }
      frequencies.push(frequency);
      if (realIndex >= 0 && imagIndex >= 0) {
        s11.push(complex(Number(columns[realIndex]), Number(columns[imagIndex])));
      } else if (dbIndex >= 0 && phaseIndex >= 0) {
        s11.push(fromDbAngle(Number(columns[dbIndex]), Number(columns[phaseIndex])));
      } else if (magnitudeIndex >= 0 && phaseIndex >= 0) {
        s11.push(fromMagnitudeAngle(Number(columns[magnitudeIndex]), Number(columns[phaseIndex])));
      } else {
        const fallbackReal = Number(columns[1]);
        const fallbackImag = Number(columns[2]);
        s11.push(complex(fallbackReal, fallbackImag));
      }
    });

    return { frequencyHz: frequencies, s11: s11, source: "CSV upload" };
  }

  function generateSampleMeasurement() {
    const start = 0.8e9;
    const stop = 3.2e9;
    const points = 201;
    const frequencyHz = [];
    const s11 = [];
    for (let index = 0; index < points; index += 1) {
      const frequency = start + ((stop - start) * index) / (points - 1);
      const normalized = frequency / 1.62e9;
      const phase = -2.2 * Math.atan(18 * (normalized - 1 / normalized));
      const notch = 0.48 / Math.sqrt(1 + Math.pow(12 * (normalized - 1 / normalized), 2));
      const magnitude = Math.max(0.12, 0.94 - notch);
      frequencyHz.push(frequency);
      s11.push(complex(magnitude * Math.cos(phase), magnitude * Math.sin(phase)));
    }
    return { frequencyHz: frequencyHz, s11: s11, source: "Built-in demo sample" };
  }

  function computeApproximatePermittivity(measurement, z0, c0) {
    const epsilonPrime = [];
    const epsilonDoublePrime = [];
    const conductivity = [];
    const lossTangent = [];

    measurement.s11.forEach((gammaValue, index) => {
      const impedance = cScale(cDiv(cAdd(complex(1, 0), gammaValue), cSub(complex(1, 0), gammaValue)), z0);
      const admittance = cDiv(complex(1, 0), impedance);
      const omega = 2 * Math.PI * Math.max(measurement.frequencyHz[index], 1);
      const epsilonReal = admittance.im / Math.max(omega * c0, 1e-18);
      const epsilonImag = admittance.re / Math.max(omega * c0, 1e-18);
      const sigmaApprox = admittance.re / Math.max(c0, 1e-18);
      epsilonPrime.push(epsilonReal);
      epsilonDoublePrime.push(epsilonImag);
      conductivity.push(sigmaApprox);
      lossTangent.push(Math.abs(epsilonImag) / Math.max(Math.abs(epsilonReal), 1e-12));
    });

    return {
      epsilonPrime: epsilonPrime,
      epsilonDoublePrime: epsilonDoublePrime,
      conductivity: conductivity,
      lossTangent: lossTangent,
    };
  }

  function metricCard(label, value) {
    return '<div class="demo-metric"><span>' + label + '</span><strong>' + value + "</strong></div>";
  }

  function updateMetrics(container, measurement, permittivity) {
    const meanEpsilonPrime =
      permittivity.epsilonPrime.reduce((sum, value) => sum + value, 0) / Math.max(permittivity.epsilonPrime.length, 1);
    const meanLoss =
      permittivity.lossTangent.reduce((sum, value) => sum + value, 0) / Math.max(permittivity.lossTangent.length, 1);
    const minMagnitude = Math.min.apply(null, measurement.s11.map(magnitudeDb));
    container.innerHTML =
      metricCard("Samples", String(measurement.frequencyHz.length)) +
      metricCard("Start", (measurement.frequencyHz[0] / 1e9).toFixed(3) + " GHz") +
      metricCard("Stop", (measurement.frequencyHz[measurement.frequencyHz.length - 1] / 1e9).toFixed(3) + " GHz") +
      metricCard("Min |S11|", minMagnitude.toFixed(2) + " dB") +
      metricCard("Mean epsilon'", meanEpsilonPrime.toFixed(2)) +
      metricCard("Mean loss tangent", meanLoss.toFixed(3));
  }

  function buildSmithCircle() {
    const x = [];
    const y = [];
    for (let degree = 0; degree <= 360; degree += 2) {
      const angle = (degree * Math.PI) / 180;
      x.push(Math.cos(angle));
      y.push(Math.sin(angle));
    }
    return { x: x, y: y };
  }

  function renderPlots(measurement, permittivity) {
    const frequencyGHz = measurement.frequencyHz.map((value) => value / 1e9);
    const smithCircle = buildSmithCircle();
    const plotLayout = {
      paper_bgcolor: "rgba(0,0,0,0)",
      plot_bgcolor: "rgba(0,0,0,0)",
      margin: { l: 52, r: 20, t: 48, b: 45 },
      font: { family: "IBM Plex Sans, sans-serif" },
    };

    window.Plotly.newPlot(
      "liteperm-demo-magnitude",
      [
        {
          x: frequencyGHz,
          y: measurement.s11.map(magnitudeDb),
          type: "scatter",
          mode: "lines",
          line: { color: "#0f766e", width: 3 },
          name: "|S11|",
        },
      ],
      Object.assign({}, plotLayout, {
        title: "S11 Magnitude",
        xaxis: { title: "Frequency (GHz)" },
        yaxis: { title: "Magnitude (dB)" },
      }),
      { responsive: true, displaylogo: false }
    );

    window.Plotly.newPlot(
      "liteperm-demo-phase",
      [
        {
          x: frequencyGHz,
          y: measurement.s11.map(phaseDeg),
          type: "scatter",
          mode: "lines",
          line: { color: "#f59e0b", width: 3 },
          name: "Phase",
        },
      ],
      Object.assign({}, plotLayout, {
        title: "S11 Phase",
        xaxis: { title: "Frequency (GHz)" },
        yaxis: { title: "Phase (deg)" },
      }),
      { responsive: true, displaylogo: false }
    );

    window.Plotly.newPlot(
      "liteperm-demo-smith",
      [
        {
          x: smithCircle.x,
          y: smithCircle.y,
          type: "scatter",
          mode: "lines",
          line: { color: "#94a3b8", dash: "dot" },
          name: "Unit circle",
        },
        {
          x: measurement.s11.map((value) => value.re),
          y: measurement.s11.map((value) => value.im),
          type: "scatter",
          mode: "lines+markers",
          line: { color: "#22c55e", width: 2 },
          marker: { size: 5 },
          name: "Gamma",
        },
      ],
      Object.assign({}, plotLayout, {
        title: "Smith Chart",
        xaxis: { title: "Real(Gamma)", scaleanchor: "y", zeroline: false },
        yaxis: { title: "Imag(Gamma)", zeroline: false },
      }),
      { responsive: true, displaylogo: false }
    );

    window.Plotly.newPlot(
      "liteperm-demo-permittivity",
      [
        {
          x: frequencyGHz,
          y: permittivity.epsilonPrime,
          type: "scatter",
          mode: "lines",
          line: { color: "#0284c7", width: 3 },
          name: "epsilon'",
        },
        {
          x: frequencyGHz,
          y: permittivity.epsilonDoublePrime,
          type: "scatter",
          mode: "lines",
          line: { color: "#ef4444", width: 3 },
          name: "epsilon''",
        },
      ],
      Object.assign({}, plotLayout, {
        title: "Permittivity Visualisation",
        xaxis: { title: "Frequency (GHz)" },
        yaxis: { title: "Approximate permittivity" },
      }),
      { responsive: true, displaylogo: false }
    );
  }

  function mountDemo(measurement, z0, c0, statusElement, metricsElement) {
    const permittivity = computeApproximatePermittivity(measurement, z0, c0);
    updateMetrics(metricsElement, measurement, permittivity);
    renderPlots(measurement, permittivity);
    statusElement.textContent =
      "Loaded " +
      measurement.source +
      ". The permittivity plot is an educational OECP-style approximation using C0 = " +
      c0.toExponential(2) +
      " F.";
  }

  document.addEventListener("DOMContentLoaded", function () {
    const root = document.getElementById("liteperm-demo-root");
    if (!root) {
      return;
    }

    const fileInput = document.getElementById("liteperm-demo-file");
    const z0Input = document.getElementById("liteperm-demo-z0");
    const c0Input = document.getElementById("liteperm-demo-c0");
    const sampleButton = document.getElementById("liteperm-demo-load-sample");
    const clearButton = document.getElementById("liteperm-demo-clear");
    const statusElement = document.getElementById("liteperm-demo-status");
    const metricsElement = document.getElementById("liteperm-demo-metrics");

    if (!window.Plotly) {
      statusElement.textContent = "Plotly.js did not load, so the browser demo is unavailable.";
      return;
    }

    function currentZ0() {
      return Number(z0Input.value) || 50;
    }

    function currentC0() {
      return Number(c0Input.value) || 1e-12;
    }

    function handleTextPayload(text, name) {
      const lowerName = name.toLowerCase();
      const measurement = lowerName.endsWith(".s1p") ? parseTouchstone(text) : parseCsv(text);
      mountDemo(measurement, currentZ0(), currentC0(), statusElement, metricsElement);
    }

    fileInput.addEventListener("change", function (event) {
      const file = event.target.files && event.target.files[0];
      if (!file) {
        return;
      }
      const reader = new FileReader();
      reader.onload = function (loadEvent) {
        try {
          handleTextPayload(String(loadEvent.target.result || ""), file.name);
        } catch (error) {
          statusElement.textContent = "Could not parse file: " + error.message;
        }
      };
      reader.readAsText(file);
    });

    sampleButton.addEventListener("click", function () {
      mountDemo(generateSampleMeasurement(), currentZ0(), currentC0(), statusElement, metricsElement);
    });

    clearButton.addEventListener("click", function () {
      ["liteperm-demo-magnitude", "liteperm-demo-phase", "liteperm-demo-smith", "liteperm-demo-permittivity"].forEach(function (plotId) {
        const plot = document.getElementById(plotId);
        if (plot) {
          plot.innerHTML = "";
        }
      });
      metricsElement.innerHTML = "";
      statusElement.textContent = "Demo cleared. Upload a Touchstone or CSV file, or load the built-in sample.";
      fileInput.value = "";
    });

    statusElement.textContent = "Upload a `.s1p` or `.csv` file, or load the built-in sample dataset.";
  });
})();
