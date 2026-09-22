#!/usr/bin/env python3
"""Draw the launcher icon, with the standard library only.

A committed binary nobody can regenerate is a binary nobody can change. This
writes both files the app needs — a PNG for the browser tab and an ICO for the
Windows shortcut — from arithmetic, so the icon is as reviewable as the rest of
the repository.

The shape is the funnel: wide at the top, narrow at the bottom, with the three
bands the pipeline actually has (free intake, the metered harness stages, the
one report that comes out).

    python scripts/make_icon.py
"""
import struct
import sys
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SIZES = (16, 32, 48, 64, 128, 256)

BACKGROUND = (0x11, 0x18, 0x27)     # the app's surface
WIDE = (0x38, 0xbd, 0xf8)           # intake: wide and cheap
NARROW = (0xfb, 0xbf, 0x24)         # the metered stages
DROP = (0x34, 0xd3, 0x99)           # what comes out


def _blend(bottom, top, alpha):
    return tuple(round(b + (t - b) * alpha) for b, t in zip(bottom, top))


def pixels(size: int) -> list:
    """One RGBA row per line. Anti-aliased by sampling each pixel four times."""
    rows = []
    radius = size * 0.18
    for y in range(size):
        row = bytearray()
        for x in range(size):
            colour, alpha = BACKGROUND, 0.0
            hits, shade = 0, [0.0, 0.0, 0.0]
            for dx, dy in ((0.25, 0.25), (0.75, 0.25), (0.25, 0.75), (0.75, 0.75)):
                fx, fy = (x + dx) / size, (y + dy) / size
                inside = _funnel(fx, fy)
                if inside is not None:
                    hits += 1
                    shade = [s + c for s, c in zip(shade, inside)]
            if hits:
                colour = _blend(BACKGROUND, tuple(c / hits for c in shade), hits / 4)
            alpha = 1.0 if _in_card(x, y, size, radius) else 0.0
            if alpha == 0.0:
                row += bytes((0, 0, 0, 0))
            else:
                row += bytes((*(round(c) for c in colour), 255))
        rows.append(bytes(row))
    return rows


def _in_card(x, y, size, radius) -> bool:
    """A rounded square, so the icon reads as an app rather than a sticker."""
    cx = min(max(x + 0.5, radius), size - radius)
    cy = min(max(y + 0.5, radius), size - radius)
    return ((x + 0.5 - cx) ** 2 + (y + 0.5 - cy) ** 2) <= radius ** 2


def _funnel(fx: float, fy: float):
    """The colour at a point in the unit square, or None for background."""
    top, throat, bottom = 0.20, 0.62, 0.84
    if fy < top or fy > bottom:
        return None
    if fy <= throat:                                   # the tapering body
        span = 0.34 - (fy - top) / (throat - top) * 0.26
        if abs(fx - 0.5) > span:
            return None
        return WIDE if fy < (top + throat) / 2 else NARROW
    if fy <= bottom:                                   # the single drop
        if abs(fx - 0.5) > 0.075:
            return None
        return DROP
    return None


def png(size: int) -> bytes:
    raw = b''.join(b'\x00' + row for row in pixels(size))

    def chunk(kind: bytes, payload: bytes) -> bytes:
        body = kind + payload
        return struct.pack('>I', len(payload)) + body + struct.pack('>I', zlib.crc32(body))

    header = struct.pack('>IIBBBBB', size, size, 8, 6, 0, 0, 0)   # 8-bit RGBA
    return (b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', header)
            + chunk(b'IDAT', zlib.compress(raw, 9)) + chunk(b'IEND', b''))


def ico(images: dict) -> bytes:
    """A PNG-payload ICO. Windows has read these since Vista."""
    entries, blobs, offset = b'', b'', 6 + 16 * len(images)
    for size in sorted(images):
        data = images[size]
        entries += struct.pack('<BBBBHHII', size % 256, size % 256, 0, 0, 1, 32,
                               len(data), offset)
        blobs += data
        offset += len(data)
    return struct.pack('<HHH', 0, 1, len(images)) + entries + blobs


def main() -> int:
    images = {size: png(size) for size in SIZES}
    assets = ROOT / 'assets'
    assets.mkdir(exist_ok=True)
    (assets / 'harness.ico').write_bytes(ico(images))
    (assets / 'harness.png').write_bytes(images[256])
    public = ROOT / 'apps' / 'web' / 'public'
    public.mkdir(parents=True, exist_ok=True)
    (public / 'icon.png').write_bytes(images[256])
    (public / 'favicon.ico').write_bytes(ico({s: images[s] for s in (16, 32, 48)}))
    for path in (assets / 'harness.ico', assets / 'harness.png',
                 public / 'icon.png', public / 'favicon.ico'):
        print(f'{path.relative_to(ROOT)}  {path.stat().st_size:,} bytes')
    return 0


if __name__ == '__main__':
    sys.exit(main())
