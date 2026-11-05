"""Provider abstraction: app logic depends only on this interface."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


class ProviderError(RuntimeError):
    """Any failure talking to a model provider (network, quota, refusal)."""


@dataclass
class ProviderResult:
    text: str
    model: str
    latency_s: float
    usage: dict[str, int] | None = None
    is_fallback: bool = False  # True means NOT real AI output


class ModelProvider(ABC):
    name: str
    is_fallback: bool = False

    @abstractmethod
    def generate(self, prompt: str, image_bytes: bytes | None = None, mime_type: str = "image/jpeg") -> ProviderResult:
        """Send a prompt (optionally with one image) and return the text reply."""
