#!/usr/bin/env python3
"""Screenshot the fixed 900x1200 HTML poster with a local Chromium browser."""

from __future__ import annotations

import argparse
import json
import os
import signal
import shutil
import struct
import subprocess
import tempfile
import time
from pathlib import Path


WIDTH, HEIGHT = 900, 1200


def browser_path() -> str | None:
    configured = os.environ.get("MARVIS_CHROMIUM_PATH")
    candidates = [
        configured,
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
        "/Applications/Chromium.app/Contents/MacOS/Chromium",
        shutil.which("google-chrome"),
        shutil.which("chromium"),
        shutil.which("chromium-browser"),
        shutil.which("microsoft-edge"),
    ]
    return next((candidate for candidate in candidates if candidate and Path(candidate).exists()), None)


def verify_png(path: Path) -> None:
    data = path.read_bytes()
    if len(data) < 24 or data[:8] != b"\x89PNG\r\n\x1a\n":
        raise SystemExit("The browser did not produce a valid PNG file.")
    image_size = struct.unpack(">II", data[16:24])
    if image_size != (WIDTH, HEIGHT):
        raise SystemExit(f"Unexpected report size {image_size}; expected {(WIDTH, HEIGHT)}.")
    if len(data) < 5000:
        raise SystemExit("The rendered report is unexpectedly small and may be blank.")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--html", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    html_path = Path(args.html).expanduser().resolve()
    output_path = Path(args.output).expanduser().resolve()
    if not html_path.exists():
        raise SystemExit(f"HTML report not found: {html_path}")
    browser = browser_path()
    if not browser:
        raise SystemExit(
            "No Chromium browser found. Install Chrome/Chromium or set MARVIS_CHROMIUM_PATH; "
            "do not replace the deterministic screenshot with AI image generation."
        )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="marvis-chrome-") as profile_dir:
        command = [
            browser,
            "--headless=new",
            "--no-sandbox",
            "--disable-gpu",
            "--disable-extensions",
            "--disable-background-networking",
            "--disable-component-update",
            "--disable-sync",
            "--hide-scrollbars",
            "--run-all-compositor-stages-before-draw",
            "--virtual-time-budget=1500",
            "--force-device-scale-factor=1",
            f"--window-size={WIDTH},{HEIGHT}",
            f"--user-data-dir={profile_dir}",
            f"--screenshot={output_path}",
            html_path.as_uri(),
        ]
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            start_new_session=True,
        )
        deadline = time.monotonic() + 15
        last_size = -1
        stable_checks = 0
        while process.poll() is None and time.monotonic() < deadline:
            size = output_path.stat().st_size if output_path.exists() else 0
            if size > 0 and size == last_size:
                stable_checks += 1
            else:
                stable_checks = 0
                last_size = size
            if stable_checks >= 3:
                os.killpg(process.pid, signal.SIGTERM)
                break
            time.sleep(0.1)
        if process.poll() is None:
            os.killpg(process.pid, signal.SIGTERM)
        try:
            _, stderr = process.communicate(timeout=3)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL)
            _, stderr = process.communicate()
        if not output_path.exists() or output_path.stat().st_size == 0:
            detail = stderr.strip()[-2000:] or f"browser exited with code {process.returncode}"
            raise SystemExit(f"Chromium screenshot failed: {detail}")
    verify_png(output_path)
    print(json.dumps({
        "report_png": str(output_path),
        "source_html": str(html_path),
        "renderer": "chromium_screenshot",
        "width": WIDTH,
        "height": HEIGHT,
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
