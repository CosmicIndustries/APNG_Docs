# Capture → APNG (Multiplatform)

A fast, scriptable tool to capture screen activity (full-screen or region) and convert it into high-quality animated PNGs (APNG) for demos, documentation, and portfolio showcases.

---

## ✦ Features

- Cross-platform screen capture (Linux, macOS, Windows)
- Region or full-screen recording
- Deterministic frame timing (FPS-controlled)
- APNG assembly via `apngasm`
- Optional compression via `apngopt`
- CLI-first → automation friendly
- Temporary frame management (auto cleanup or retain)

---

## ✦ Use Cases

- Portfolio demos (UI workflows, scripts, tools)
- Debug/bug reproduction capture
- Documentation visuals
- Lightweight alternative to video/GIF

---

## ✦ Installation

### 1. Python dependencies
```bash
pip install pillow mss
