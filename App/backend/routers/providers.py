"""
routers/providers.py
Centralized AI provider pool for Polynovea.

Supports:
  - Multiple NVIDIA NIM keys (NVIDIA_API_KEY, NVIDIA_API_KEY_2, ..., or NVIDIA_API_KEYS=k1,k2,k3)
  - Mistral API (MISTRAL_API_KEY, optional MISTRAL_MODEL)

Key rotation is round-robin — spreads load evenly across all configured keys
so no single key bears the full RPM/TPM quota.
"""

import itertools
import os
from dataclasses import dataclass

from openai import AsyncOpenAI

_NVIDIA_BASE  = "https://integrate.api.nvidia.com/v1"
_MISTRAL_BASE = "https://api.mistral.ai/v1"

_DEFAULT_MISTRAL_MODEL = "mistral-large-latest"


# ─── NVIDIA key pool ──────────────────────────────────────────────────────────

def _load_nvidia_keys() -> list[str]:
    seen: set[str] = set()
    keys: list[str] = []

    def _add(k: str) -> None:
        k = k.strip()
        if k and k not in seen:
            seen.add(k)
            keys.append(k)

    # Primary key (backward-compatible)
    _add(os.getenv("NVIDIA_API_KEY", ""))

    # Comma-separated batch: NVIDIA_API_KEYS=key1,key2,key3
    for k in os.getenv("NVIDIA_API_KEYS", "").split(","):
        _add(k)

    # Numbered extras: NVIDIA_API_KEY_2, NVIDIA_API_KEY_3, ...
    for i in range(2, 20):
        _add(os.getenv(f"NVIDIA_API_KEY_{i}", ""))

    return keys


_nvidia_keys: list[str] = _load_nvidia_keys()
_nvidia_cycle = itertools.cycle(_nvidia_keys) if _nvidia_keys else None


def next_nvidia_key() -> str | None:
    """Return the next NVIDIA key in round-robin order, or None if none configured."""
    return next(_nvidia_cycle) if _nvidia_cycle else None


def nvidia_key_count() -> int:
    return len(_nvidia_keys)


# ─── Mistral ──────────────────────────────────────────────────────────────────

def mistral_key() -> str:
    return os.getenv("MISTRAL_API_KEY", "")


def mistral_model() -> str:
    return os.getenv("MISTRAL_MODEL", _DEFAULT_MISTRAL_MODEL)


def mistral_available() -> bool:
    return bool(mistral_key())


# ─── Client factories ─────────────────────────────────────────────────────────

@dataclass
class ProviderClient:
    client: AsyncOpenAI
    model:  str
    name:   str          # "nvidia" | "mistral"
    key_hint: str        # last 6 chars of key, for log tracing


def get_nvidia_client(model: str) -> ProviderClient | None:
    """Return an AsyncOpenAI client pointed at NVIDIA NIM with the next key in the pool."""
    key = next_nvidia_key()
    if not key:
        return None
    return ProviderClient(
        client=AsyncOpenAI(api_key=key, base_url=_NVIDIA_BASE),
        model=model,
        name="nvidia",
        key_hint=key[-6:],
    )


def get_mistral_client() -> ProviderClient | None:
    """Return an AsyncOpenAI client pointed at Mistral API, or None if not configured."""
    key = mistral_key()
    if not key:
        return None
    return ProviderClient(
        client=AsyncOpenAI(api_key=key, base_url=_MISTRAL_BASE),
        model=mistral_model(),
        name="mistral",
        key_hint=key[-6:],
    )


# ─── Fast-mode provider selection ────────────────────────────────────────────
# For single-call streaming (chat, campaign, whatsapp, brief generator).
# Cycles: NVIDIA key 1 → NVIDIA key 2 → ... → Mistral (if configured) → repeat.

_fast_providers: list[str] = []   # "nvidia" repeated N times, then "mistral" if present

def _build_fast_cycle() -> itertools.cycle | None:
    providers: list[str] = ["nvidia"] * len(_nvidia_keys)
    if mistral_available():
        providers.append("mistral")
    if not providers:
        return None
    return itertools.cycle(providers)

_fast_cycle = _build_fast_cycle()


def next_fast_client(nvidia_model: str) -> ProviderClient | None:
    """
    Return the next provider for fast-mode (single streaming call).
    Rotates across all NVIDIA keys then Mistral, evenly.
    Falls back to any available provider if the selected one has no key.
    """
    if _fast_cycle is None:
        return None

    provider = next(_fast_cycle)
    if provider == "mistral":
        client = get_mistral_client()
        if client:
            return client
        # Mistral key removed at runtime — fall back to NVIDIA
        return get_nvidia_client(nvidia_model)
    else:
        client = get_nvidia_client(nvidia_model)
        if client:
            return client
        # No NVIDIA keys — fall back to Mistral
        return get_mistral_client()
