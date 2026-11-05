"""Phase 1 skeleton: upload, preview, call provider, show raw output. No styling yet."""
from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).parent / "src"))

from civiclens.config import ConfigError  # noqa: E402
from civiclens.providers import ProviderError, get_provider  # noqa: E402

st.title("CivicLens (skeleton)")
try:
    provider = get_provider()
except (ConfigError, ValueError) as exc:
    st.error(str(exc))
    st.stop()
if provider.is_fallback:
    st.warning("DEMONSTRATION FALLBACK active: output is canned, not real AI.")

up = st.file_uploader("Upload a photo", type=["jpg", "jpeg", "png"])
if up:
    data = up.getvalue()
    st.image(data)
    if st.button("Analyze"):
        try:
            res = provider.generate("Describe what is visible in this image in two sentences.", data, up.type or "image/jpeg")
            st.code(res.text)
            st.caption(f"model={res.model} latency={res.latency_s:.2f}s")
        except ProviderError as exc:
            st.error(str(exc))
