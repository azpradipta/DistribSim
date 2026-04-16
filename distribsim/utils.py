import math
import time
import random


def bezier(sx, sy, cx, cy, dx, dy, t):
    """Hitung titik pada kurva quadratic bezier. t ∈ [0.0, 1.0]"""
    u = 1 - t
    return (
        u * u * sx + 2 * u * t * cx + t * t * dx,
        u * u * sy + 2 * u * t * cy + t * t * dy,
    )


def lerp(a, b, t):
    """Linear interpolation antara a dan b dengan faktor t."""
    return a + (b - a) * t


def clamp(v, lo, hi):
    """Batasi nilai v dalam rentang [lo, hi]."""
    return min(max(v, lo), hi)


def fmt_ms(ms):
    """Format millisecond ke string yang mudah dibaca."""
    if ms < 1:
        return "<1ms"
    return f"{ms:.0f}ms"


def now():
    """Waktu saat ini dalam millisecond."""
    return time.time() * 1000


def rand(lo, hi):
    """Bilangan acak float dalam rentang [lo, hi]."""
    return lo + random.random() * (hi - lo)


def hex_to_rgb(h):
    """Konversi hex color string ke tuple (r, g, b)."""
    h = h.lstrip('#')
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def blend_color(color, alpha, bg="#060710"):
    """
    Blend warna foreground dengan background pada alpha tertentu (0.0–1.0).
    Digunakan untuk efek glow dan transparansi pada canvas.
    """
    try:
        cr, cg, cb = hex_to_rgb(color)
        br, bg_g, bb = hex_to_rgb(bg)
        r = int(cr * alpha + br * (1 - alpha))
        g = int(cg * alpha + bg_g * (1 - alpha))
        b = int(cb * alpha + bb * (1 - alpha))
        return f"#{r:02x}{g:02x}{b:02x}"
    except Exception:
        return color
