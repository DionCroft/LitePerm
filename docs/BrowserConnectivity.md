# Browser Connectivity Investigation

_Prepared for LitePerm Phase 4 on May 29, 2026._

## Summary

Direct browser-side LiteVNA communication is **promising but not yet production-ready**.

The most realistic near-term path is **Web Serial**, provided the LiteVNA presents itself to the operating system as a virtual serial device. This is an inference from LitePerm's current desktop architecture, which already communicates with LiteVNA-style devices through serial interfaces.

`WebUSB` remains a secondary option for future work if direct vendor-specific USB access is needed.

## Browser Feasibility

### Web Serial

- Best match for LitePerm's current USB serial workflow
- Suitable when the device appears as a serial port
- Requires a secure context and explicit user permission
- Best treated as a **Chromium-first** roadmap item

### WebUSB

- Lower-level hardware path
- More relevant if raw USB access is needed instead of a virtual COM port
- Also limited availability and secure-context only
- More protocol work would be required before LitePerm could rely on it

## Supported Browsers

Based on MDN guidance as of May 29, 2026:

- treat both APIs as **limited availability**
- plan for **recent Chromium-based browsers first**
- do not assume Firefox or Safari support for core LitePerm browser acquisition flows

## Security Requirements

- the site must run in a **secure context**
- GitHub Pages over `https://` qualifies
- `localhost` is also considered trustworthy for development
- the user must explicitly grant device permission

## Practical Limitations

- browser compatibility is incomplete
- serial and USB permissions are user-driven
- background and multi-device workflows need careful UX design
- protocol verification with a real LiteVNA is still required before promising browser capture

## Recommended Development Plan

1. Keep the current browser feature set file-based only
2. Add a small experimental Web Serial branch behind a clear warning
3. Test LiteVNA enumeration on Chromium with real hardware
4. Validate sweep commands, partial reads, and error recovery
5. Add browser acquisition only after hardware verification is complete

## Recommendation for Phase 4

Do **not** ship full browser acquisition yet.

Ship:

- GitHub Pages documentation
- browser-side upload and visualisation
- browser connectivity documentation

Defer:

- direct LiteVNA browser capture
- browser-side calibration storage
- browser-side inverse modelling linked to live hardware
