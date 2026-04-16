"""
distribsim/draw_engine.py
Mesin rendering canvas: DrawEngine dan ParticleSystem.

DrawEngine menangani semua operasi drawing pada tkinter Canvas:
- Background dot-grid
- Node dengan glow, pulse, state badge
- Koneksi bezier antar node (garis putus-putus)
- Paket bergerak dengan trail effect
- Label teks dan arah panah

ParticleSystem membuat efek burst/explosion saat paket tiba.
"""

import tkinter as tk
import math

from .config import (
    BG_DARK, COLOR_ERR, COLOR_OK, COLOR_WARN,
    TEXT_2, CANVAS_W, CANVAS_H,
)
from .utils import bezier, blend_color, rand


class DrawEngine:
    """Semua operasi drawing pada tkinter Canvas untuk satu simulasi."""

    def __init__(self, canvas: tk.Canvas):
        self.canvas = canvas
        self.W = CANVAS_W
        self.H = CANVAS_H

    def clear(self):
        """Bersihkan seluruh canvas."""
        self.canvas.delete("all")

    def draw_bg(self):
        """Background gelap dengan pola dot-grid."""
        self.canvas.create_rectangle(0, 0, self.W, self.H, fill=BG_DARK, outline="")
        gap = 30
        for y in range(gap, self.H, gap):
            for x in range(gap, self.W, gap):
                self.canvas.create_oval(x - 1, y - 1, x + 1, y + 1, fill="#1a1d30", outline="")

    def draw_node(self, nd, t: float = 0):
        """
        Gambar node sebagai lingkaran dengan efek glow dan animasi state.
        nd = NodeDef, t = waktu animasi (ms) untuk pulse.
        """
        x, y, r = nd.x, nd.y, nd.radius
        color, state = nd.color, nd.state

        # Efek pulse berdasarkan state
        pulse = 1.0
        if state == "processing":
            pulse = 1 + 0.07 * math.sin(t * 0.008)
        elif state == "active":
            pulse = 1 + 0.04 * math.sin(t * 0.004)
        rp = r * pulse

        # Outer glow (hanya saat tidak idle)
        if state != "idle":
            for i in range(3, 0, -1):
                gr = rp + i * 8
                c = blend_color(color, 0.06 / i)
                self.canvas.create_oval(x - gr, y - gr, x + gr, y + gr, fill=c, outline="")

        # Pulse ring
        if state in ("active", "processing"):
            ring_r = rp * 1.5
            self.canvas.create_oval(x - ring_r, y - ring_r, x + ring_r, y + ring_r,
                                    fill="", outline=blend_color(color, 0.4), width=2)

        # Isi dan border lingkaran
        fill_c = blend_color(COLOR_ERR if state == "error" else color, 0.18)
        self.canvas.create_oval(x - rp, y - rp, x + rp, y + rp, fill=fill_c, outline="")
        border_c = COLOR_ERR if state == "error" else color
        self.canvas.create_oval(x - rp, y - rp, x + rp, y + rp,
                                fill="", outline=border_c, width=2.5 if state == "idle" else 3)

        # Highlight tengah
        hl_r = rp * 0.35
        self.canvas.create_oval(x - hl_r, y - hl_r - rp * 0.2,
                                x + hl_r, y + hl_r - rp * 0.2,
                                fill=blend_color(color, 0.25), outline="")

        # Teks label
        self.canvas.create_text(x, y, text=nd.label, fill="white",
                                font=("Inter", 9, "bold"), anchor="center")
        self.canvas.create_text(x, y + rp + 13, text=nd.sublabel, fill=color,
                                font=("Consolas", 7), anchor="center")

        # State badge (pojok kanan atas)
        if state != "idle":
            badge_text = {"active": "●", "processing": "⟳", "error": "✗"}.get(state, "")
            badge_c    = {"active": COLOR_OK, "processing": COLOR_WARN,
                          "error": COLOR_ERR}.get(state, color)
            self.canvas.create_text(x + rp - 4, y - rp + 4,
                                    text=badge_text, fill=badge_c, font=("Arial", 8, "bold"))

    def draw_connection(self, sx, sy, dx, dy, cx, cy, color, dash=(6, 5)):
        """Gambar garis koneksi bezier antar dua node (putus-putus)."""
        pts = []
        c = blend_color(color, 0.28)
        for i in range(31):
            bx, by = bezier(sx, sy, cx, cy, dx, dy, i / 30)
            pts.extend([bx, by])
        if len(pts) >= 4:
            self.canvas.create_line(*pts, fill=c, width=1.5, smooth=True, dash=dash)

    def draw_packet(self, pkt):
        """Gambar paket bergerak dengan trail (jejak) effect."""
        if pkt.done:
            return
        x, y = bezier(pkt.sx, pkt.sy, pkt.cx, pkt.cy, pkt.dx, pkt.dy, pkt.t)

        # Trail
        for i in range(5, 0, -1):
            ti = max(0, pkt.t - i * 0.02)
            tx, ty = bezier(pkt.sx, pkt.sy, pkt.cx, pkt.cy, pkt.dx, pkt.dy, ti)
            tc = blend_color(pkt.color, (1 - i / 5) * 0.4)
            tr = pkt.radius * (0.3 + 0.7 * (1 - i / 5))
            self.canvas.create_oval(tx - tr, ty - tr, tx + tr, ty + tr, fill=tc, outline="")

        # Paket utama
        r = pkt.radius
        self.canvas.create_oval(x - r, y - r, x + r, y + r,
                                fill=pkt.color, outline="white", width=1)
        if pkt.label:
            self.canvas.create_text(x, y, text=pkt.label[:5], fill="black",
                                    font=("Consolas", 7, "bold"), anchor="center")

    def draw_arrow_label(self, x, y, text, color, anchor="center"):
        """Label arah panah komunikasi."""
        self.canvas.create_text(x, y, text=text, fill=blend_color(color, 0.55),
                                font=("Consolas", 8), anchor=anchor)

    def draw_text_label(self, x, y, text, color=TEXT_2, size=9, bold=False):
        """Teks label informatif di canvas."""
        self.canvas.create_text(x, y, text=text, fill=color,
                                font=("Inter", size, "bold" if bold else "normal"),
                                anchor="center")


class ParticleSystem:
    """Sistem partikel untuk efek burst saat paket tiba di node."""

    def __init__(self, canvas: tk.Canvas):
        self.canvas    = canvas
        self.particles = []

    def spawn(self, x, y, color, count=10):
        """Buat partikel baru yang menyebar dari titik (x, y)."""
        import math, random
        for _ in range(count):
            angle = random.uniform(0, math.pi * 2)
            speed = rand(0.5, 3.0)
            self.particles.append({
                'x': x, 'y': y,
                'vx': math.cos(angle) * speed,
                'vy': math.sin(angle) * speed,
                'color': color,
                'life': rand(20, 50),
                'max_life': 50,
            })

    def update_draw(self):
        """Update posisi partikel dan gambar ke canvas."""
        alive = []
        for p in self.particles:
            p['x'] += p['vx']
            p['y'] += p['vy']
            p['vy'] += 0.06      # gravitasi
            p['life'] -= 1
            if p['life'] <= 0:
                continue
            alpha = p['life'] / p['max_life']
            r = 2.5 * alpha
            self.canvas.create_oval(
                p['x'] - r, p['y'] - r, p['x'] + r, p['y'] + r,
                fill=blend_color(p['color'], alpha), outline=""
            )
            alive.append(p)
        self.particles = alive
