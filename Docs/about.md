System dependencies
Tool Purpose Install
apngasm Build APNG sudo apt install apngasm or brew install apngasm
apngopt Optimize (optional) Same as above or build from source

Windows:

Download binaries from GitHub releases and add to PATH
✦ Quick Start
Full screen (10s @ 10 FPS)
python capture_to_apng.py -o demo.png -d 10 -f 10
Region capture
python capture_to_apng.py -o demo.png -d 5 -f 15 -r 100 200 1280 720
With optimization
python capture_to_apng.py -o demo.png -d 8 -f 12 --optimize
Keep raw frames
python capture_to_apng.py -o demo.png -d 5 --keep-frames
✦ CLI Arguments
Flag Description
-o, --output Output APNG file
-d, --duration Duration in seconds
-f, --fps Frames per second
-r, --region Capture region (LEFT TOP WIDTH HEIGHT)
--optimize Run apngopt after build
--keep-frames Do not delete raw frames
--frames-dir Custom frame directory
--delay Countdown before capture
✦ Pipeline Overview
Screen → Frame Capture (mss)
→ PNG Frames (Pillow)
→ APNG Assembly (apngasm)
→ Optimization (apngopt)
✦ Example Output
[INFO] Capturing 120 frames @ 12 fps
[DONE] demo.png (842 KB, 120 frames @ 12 fps)
[OPT] Optimized: 842 KB → 620 KB (26.4% saved)
✦ Performance Notes
CPU-bound during PNG encoding
Disk I/O spikes with high FPS + large regions
Optimal range:
8–15 FPS (smooth enough for demos)
≤ 1080p capture for portability
✦ Known Limitations
No audio capture (by design)
No hardware encoding (PNG only)
Multi-monitor defaults to primary display
Very high FPS may drift slightly due to OS scheduling
✦ Roadmap
Multi-monitor selection
Cursor highlighting overlay
Frame diff compression (delta encoding)
Direct video → APNG pipeline
Web UI wrapper
✦ License

MIT (or specify your own)

✦ Author

Built for high-signal portfolio capture workflows.

---

# 📄 `docs.md` (Technical Documentation)

````markdown
# Technical Documentation — Capture → APNG

---

## 1. System Architecture

### 1.1 Capture Layer

- Library: `mss`
- Method: direct framebuffer grab
- Output: raw BGRA buffer → converted to RGB

### 1.2 Frame Encoding

- Library: `Pillow`
- Format: PNG (lossless)
- Naming: zero-padded sequential indexing

### 1.3 Assembly Layer

- Tool: `apngasm`
- Input: ordered PNG frames
- Output: animated PNG

### 1.4 Optimization Layer (Optional)

- Tool: `apngopt`
- Method: frame deduplication + compression

---

## 2. Timing Model

Frame pacing uses:

interval = 1 / fps
sleep = interval - processing_time

### Constraints

- Non-realtime OS scheduling → slight drift
- High FPS (>30) increases jitter risk
- Disk latency impacts consistency

---

## 3. Frame Pipeline

for frame in N:
capture()
convert()
save()
sleep()

### Bottlenecks

| Stage   | Cost Driver        |
| ------- | ------------------ |
| Capture | Screen resolution  |
| Convert | CPU (memory copy)  |
| Save    | Disk write latency |

---

## 4. APNG Assembly Mechanics

### Delay Representation

APNG uses rational timing:

delay = delay_num / delay_den

Implementation:

delay_num = 1
delay_den = fps

---

## 5. Failure Modes

### 5.1 Missing Dependencies

- `apngasm` not in PATH → hard fail
- `apngopt` missing → soft warning

### 5.2 Frame Loss

- Occurs under:
  - High FPS
  - CPU saturation
  - Slow disk

### 5.3 Assembly Failure

Fallback strategy:

1. Glob input (`frame_*.png`)
2. Explicit file list

---

## 6. Resource Management

### Temporary Storage

- Default: system temp directory
- Optional: user-defined directory

Cleanup logic:

if keep_frames:
retain
else:
delete

---

## 7. Optimization Tradeoffs

| Mode      | Size  | Time   | Use Case     |
| --------- | ----- | ------ | ------------ |
| Raw       | Large | Fast   | Debugging    |
| Optimized | Small | Slower | Distribution |

---

## 8. Cross-Platform Notes

| OS      | Notes                     |
| ------- | ------------------------- |
| Linux   | Best performance          |
| macOS   | Stable, slight overhead   |
| Windows | Works, PATH issues common |

---

## 9. Extensibility Points

### 9.1 Capture Enhancements

- Window-specific capture
- Multi-monitor selection
- GPU-assisted capture

### 9.2 Encoding Improvements

- Parallel frame encoding
- Delta-frame storage

### 9.3 Output Options

- GIF fallback
- WebP animation
- MP4 export

---

## 10. Security Considerations

- Captures **everything on screen**
- No sandboxing
- Avoid sensitive data exposure

---

## 11. Performance Heuristics (Recommended Defaults)

| Scenario    | FPS   | Resolution |
| ----------- | ----- | ---------- |
| UI demo     | 10–12 | 1080p      |
| Fast motion | 15–20 | 720p       |
| Lightweight | 8–10  | 720p       |

---

## 12. Debug Strategy

### Enable frame retention

```bash
--keep-frames
Inspect:
Missing frames
Ordering issues
Encoding artifacts
13. Future Direction (Advanced)
13.1 Delta Encoding

Store only pixel differences → major size reduction

13.2 Async Pipeline

Decouple capture + encoding:

capture_thread → queue → encoder_thread
13.3 GPU Path

Use hardware acceleration for:

Capture
Compression
14. Summary

This tool is optimized for:

Deterministic capture
Minimal dependencies
High portability
Portfolio-grade output quality

Tradeoffs are intentionally made in favor of:

Simplicity
Reliability
Scriptability
```
````
