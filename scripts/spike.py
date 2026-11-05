"""AI spike: one image + trivial prompt, then a short Hindi generation. Usage: python scripts/spike.py [image]"""
from __future__ import annotations

import mimetypes
import sys
from pathlib import Path

for _s in (sys.stdout, sys.stderr):
    _s.reconfigure(encoding="utf-8", errors="replace")  # Hindi output on Windows consoles

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from civiclens.config import ConfigError
from civiclens.providers import ProviderError, get_provider


def main() -> int:
    try:
        provider = get_provider()
    except (ConfigError, ValueError) as exc:
        print(f"CONFIG ERROR: {exc}")
        return 2
    if provider.is_fallback:
        print("*** DEMONSTRATION FALLBACK ACTIVE: output below is NOT real AI. ***")

    image_bytes, mime = None, "image/jpeg"
    if len(sys.argv) > 1:
        path = Path(sys.argv[1])
        image_bytes = path.read_bytes()
        mime = mimetypes.guess_type(path.name)[0] or "image/jpeg"
    else:
        print("No image given; running text-only. Add a sample to data/samples/ and pass its path.")

    tests = [
        ("IMAGE", "Describe in two sentences what is visible in this image. Do not guess beyond what you can see.", image_bytes),
        ("HINDI", "Write two polite sentences in Hindi (Devanagari) reporting a pothole on a road to a municipal office.", None),
    ]
    for label, prompt, img in tests:
        if label == "IMAGE" and img is None:
            continue
        try:
            r = provider.generate(prompt, img, mime)
        except ProviderError as exc:
            print(f"[{label}] PROVIDER ERROR: {exc}")
            return 1
        print(f"[{label}] model={r.model} latency={r.latency_s:.2f}s usage={r.usage} fallback={r.is_fallback}")
        print(r.text, "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
