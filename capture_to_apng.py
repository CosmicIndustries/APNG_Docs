#!/usr/bin/env python3
"""
capture_to_apng_multiplatform.py
─────────────────────────────────
Portfolio/demo APNG capture tool.
Captures full-screen or a defined region, assembles frames into an APNG
via apngasm, and optionally optimizes with apngopt.

Dependencies (install as needed):
  pip install pillow mss
  System: apngasm, apngopt (optional)

Usage examples:
  # Full-screen, 10 seconds at 10 fps
  python capture_to_apng.py -o demo.png -d 10 -f 10

  # Region capture (x y w h)
  python capture_to_apng.py -o demo.png -d 5 -f 15 -r 100 200 1280 720

  # With optimization
  python capture_to_apng.py -o demo.png -d 8 -f 12 --optimize

  # Keep raw frames (skip cleanup)
  python capture_to_apng.py -o demo.png -d 5 --keep-frames
"""

import argparse
import os
import platform
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path


# ─── Dependency checks ────────────────────────────────────────────────────────

def require_python_dep(name: str):
    try:
        __import__(name)
    except ImportError:
        print(f"[ERROR] Missing Python package: {name}")
        print(f"        Install with: pip install {name}")
        sys.exit(1)


def require_binary(name: str, hint: str = ""):
    if shutil.which(name) is None:
        msg = f"[ERROR] Required binary not found: {name}"
        if hint:
            msg += f"\n        {hint}"
        print(msg)
        sys.exit(1)


def check_optional_binary(name: str) -> bool:
    return shutil.which(name) is not None


# ─── Screen capture ───────────────────────────────────────────────────────────

def capture_frames(
    output_dir: Path,
    fps: int,
    duration: float,
    region: tuple | None,
) -> list[Path]:
    """
    Capture frames using mss (fast cross-platform screen grab).
    region: (left, top, width, height) or None for full screen
    Returns list of saved PNG paths in order.
    """
    import mss
    from PIL import Image

    frame_paths: list[Path] = []
    interval = 1.0 / fps
    total_frames = int(fps * duration)
    pad = len(str(total_frames))

    with mss.mss() as sct:
        monitor = sct.monitors[1]  # primary monitor

        if region is not None:
            left, top, width, height = region
            capture_area = {
                "left": left,
                "top": top,
                "width": width,
                "height": height,
            }
        else:
            capture_area = monitor

        print(
            f"[INFO] Capturing {total_frames} frames "
            f"@ {fps} fps over {duration:.1f}s …"
        )

        for i in range(total_frames):
            t0 = time.perf_counter()

            shot = sct.grab(capture_area)
            img = Image.frombytes("RGB", shot.size, shot.bgra, "raw", "BGRX")

            frame_path = output_dir / f"frame_{i:0{pad}d}.png"
            img.save(frame_path, format="PNG", optimize=False)
            frame_paths.append(frame_path)

            elapsed = time.perf_counter() - t0
            remaining = interval - elapsed
            if remaining > 0:
                time.sleep(remaining)

            # Progress indicator
            pct = int((i + 1) / total_frames * 40)
            bar = "█" * pct + "░" * (40 - pct)
            print(f"\r  [{bar}] {i+1}/{total_frames}", end="", flush=True)

    print()  # newline after progress bar
    print(f"[INFO] {len(frame_paths)} frames saved to {output_dir}")
    return frame_paths


# ─── APNG assembly ────────────────────────────────────────────────────────────

def assemble_apng(
    frame_dir: Path,
    frame_paths: list[Path],
    output_path: Path,
    fps: int,
) -> bool:
    """
    Calls apngasm to assemble frames into an APNG.
    Frame delay = 1/fps seconds → expressed as delay_num/delay_den.
    """
    delay_num = 1
    delay_den = fps

    # apngasm can take a glob or explicit file list
    # Use explicit list to guarantee order
    args = [
        "apngasm",
        str(output_path),
        str(frame_dir / "frame_*.png"),
        str(delay_num),
        str(delay_den),
    ]

    # apngasm v3+ uses different CLI; try both styles
    try:
        result = subprocess.run(
            args, capture_output=True, text=True, timeout=300
        )
        if result.returncode == 0:
            return True
        # Fallback: pass files explicitly (some builds need this)
        args_explicit = ["apngasm", str(output_path)] + [
            str(p) for p in frame_paths
        ] + [str(delay_num), str(delay_den)]
        result2 = subprocess.run(
            args_explicit, capture_output=True, text=True, timeout=300
        )
        if result2.returncode == 0:
            return True
        print(f"[ERROR] apngasm failed:\n{result2.stderr}")
        return False
    except subprocess.TimeoutExpired:
        print("[ERROR] apngasm timed out.")
        return False
    except FileNotFoundError:
        print("[ERROR] apngasm not found in PATH.")
        return False


# ─── Optimization ─────────────────────────────────────────────────────────────

def optimize_apng(apng_path: Path) -> bool:
    """Run apngopt on the assembled APNG in-place."""
    tmp = apng_path.with_suffix(".opt.png")
    try:
        result = subprocess.run(
            ["apngopt", str(apng_path), str(tmp)],
            capture_output=True, text=True, timeout=300,
        )
        if result.returncode == 0 and tmp.exists():
            orig_size = apng_path.stat().st_size
            opt_size = tmp.stat().st_size
            savings = (1 - opt_size / orig_size) * 100
            tmp.replace(apng_path)
            print(f"[OPT]  Optimized: {orig_size//1024} KB → "
                  f"{opt_size//1024} KB ({savings:.1f}% saved)")
            return True
        else:
            print(f"[WARN] apngopt failed: {result.stderr.strip()}")
            if tmp.exists():
                tmp.unlink()
            return False
    except subprocess.TimeoutExpired:
        print("[WARN] apngopt timed out — skipping optimization.")
        return False


# ─── CLI ──────────────────────────────────────────────────────────────────────

def parse_args():
    p = argparse.ArgumentParser(
        description="Capture screen to APNG for portfolio/demo use.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    p.add_argument("-o", "--output", required=True,
                   help="Output APNG path (e.g. demo.png)")
    p.add_argument("-d", "--duration", type=float, default=10.0,
                   help="Capture duration in seconds (default: 10)")
    p.add_argument("-f", "--fps", type=int, default=10,
                   help="Frames per second (default: 10)")
    p.add_argument("-r", "--region", type=int, nargs=4,
                   metavar=("LEFT", "TOP", "WIDTH", "HEIGHT"),
                   help="Capture region in pixels; omit for full screen")
    p.add_argument("--optimize", action="store_true",
                   help="Run apngopt after assembly (requires apngopt in PATH)")
    p.add_argument("--keep-frames", action="store_true",
                   help="Keep raw PNG frames instead of deleting them")
    p.add_argument("--frames-dir",
                   help="Directory for temporary frames (default: system temp)")
    p.add_argument("--delay", type=float, default=3.0,
                   help="Countdown delay before capture starts (default: 3s)")
    return p.parse_args()


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    args = parse_args()

    # Dependency checks
    require_python_dep("mss")
    require_python_dep("PIL")
    require_binary("apngasm",
        hint="Install via: sudo apt install apngasm  |  brew install apngasm  |  "
             "https://github.com/apngasm/apngasm/releases (Windows)")

    if args.optimize and not check_optional_binary("apngopt"):
        print("[WARN] --optimize requested but apngopt not found; skipping.")
        args.optimize = False

    output_path = Path(args.output).expanduser().resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Countdown
    if args.delay > 0:
        print(f"[INFO] Starting capture in {args.delay:.0f}s — switch to target window …")
        for i in range(int(args.delay), 0, -1):
            print(f"       {i} …", flush=True)
            time.sleep(1)

    # Temp frame directory
    if args.frames_dir:
        frame_dir = Path(args.frames_dir).expanduser().resolve()
        frame_dir.mkdir(parents=True, exist_ok=True)
        owns_temp = False
    else:
        _tmpdir = tempfile.mkdtemp(prefix="apng_frames_")
        frame_dir = Path(_tmpdir)
        owns_temp = True

    region = tuple(args.region) if args.region else None

    try:
        # Capture
        t_start = time.time()
        frame_paths = capture_frames(
            frame_dir, args.fps, args.duration, region
        )
        t_cap = time.time() - t_start
        print(f"[INFO] Capture done in {t_cap:.1f}s")

        if not frame_paths:
            print("[ERROR] No frames captured.")
            sys.exit(1)

        # Assemble
        print(f"[INFO] Assembling APNG → {output_path} …")
        ok = assemble_apng(frame_dir, frame_paths, output_path, args.fps)
        if not ok:
            print("[ERROR] APNG assembly failed.")
            sys.exit(1)

        size_kb = output_path.stat().st_size // 1024
        print(f"[DONE] {output_path}  ({size_kb} KB, "
              f"{len(frame_paths)} frames @ {args.fps} fps)")

        # Optimize
        if args.optimize:
            print("[OPT]  Running apngopt …")
            optimize_apng(output_path)

    finally:
        if not args.keep_frames:
            if owns_temp:
                shutil.rmtree(frame_dir, ignore_errors=True)
            else:
                for f in frame_dir.glob("frame_*.png"):
                    f.unlink(missing_ok=True)
            print("[INFO] Temporary frames cleaned up.")
        else:
            print(f"[INFO] Frames retained in: {frame_dir}")


if __name__ == "__main__":
    main()
