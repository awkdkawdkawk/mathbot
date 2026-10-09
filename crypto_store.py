"""Зберігання стану з опціональним шифруванням (AES-256-GCM).

Якщо задано змінну STATE_KEY (base64, 32 байти) — файл на диску зберігає
шифроблок, який неможливо прочитати без ключа. Без ключа — звичайний JSON
(зручно для локальної розробки).
"""
from __future__ import annotations

import base64
import json
import os
from pathlib import Path

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

_NONCE = 12


def _key() -> bytes | None:
    raw = os.getenv("STATE_KEY")
    if not raw:
        return None
    return base64.b64decode(raw)


def load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    raw = path.read_bytes()
    key = _key()
    if key is None:
        try:
            return json.loads(raw.decode("utf-8"))
        except (ValueError, UnicodeDecodeError):
            return {}
    try:
        blob = base64.b64decode(raw)
        plaintext = AESGCM(key).decrypt(blob[:_NONCE], blob[_NONCE:], None)
        return json.loads(plaintext.decode("utf-8"))
    except Exception:
        return {}


def save_json(path: Path, data: dict) -> None:
    payload = json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")
    key = _key()
    if key is None:
        path.write_bytes(payload)
        return
    # не перезаписуємо, якщо дані не змінилися (щоб не засмічувати історію git)
    if load_json(path) == data:
        return
    nonce = os.urandom(_NONCE)
    ciphertext = AESGCM(key).encrypt(nonce, payload, None)
    path.write_bytes(base64.b64encode(nonce + ciphertext))
