"""
distribsim/base_sim.py
Kelas dasar simulasi dengan animation loop 60fps.

Semua simulasi (RR, PS, RPC) mewarisi BaseSimulation.
Loop berjalan via canvas.after(16ms) ≈ 60fps.
"""

import tkinter as tk
from typing import List

from .data_models import Packet
from .draw_engine import DrawEngine, ParticleSystem
from .config import COLOR_RR


class BaseSimulation:
    """
    Kelas dasar untuk semua model simulasi komunikasi.
    Subclass wajib mengimplementasikan render(t).
    """

    def __init__(self, canvas: tk.Canvas):
        self.canvas   = canvas
        self.draw     = DrawEngine(canvas)
        self.ptcl     = ParticleSystem(canvas)
        self.packets: List[Packet] = []
        self.time_ms  = 0
        self._anim_id = None
        self._running = False

    # ----------------------------------------------------------------
    # Animation Loop
    # ----------------------------------------------------------------

    def _tick(self):
        """Satu frame: update state → clear canvas → render."""
        self.time_ms += 16
        self.draw.clear()
        self.draw.draw_bg()
        self._update_packets()
        self.render(self.time_ms)
        self.ptcl.update_draw()
        if self._running:
            self._anim_id = self.canvas.after(16, self._tick)

    def _update_packets(self):
        """Majukan semua paket satu langkah; panggil on_arrive jika sudah sampai."""
        alive = []
        for p in self.packets:
            if p.done:
                continue
            p.t = min(p.t + p.speed, 1.0)
            self.draw.draw_packet(p)
            if p.t >= 1.0 and not p.done:
                p.done = True
                if p.on_arrive:
                    p.on_arrive()
            else:
                alive.append(p)
        self.packets = alive

    def start(self):
        """Mulai animation loop."""
        self._running = True
        self._tick()

    def stop(self):
        """Hentikan animation loop."""
        self._running = False
        if self._anim_id:
            self.canvas.after_cancel(self._anim_id)

    # ----------------------------------------------------------------
    # Interface untuk Subclass
    # ----------------------------------------------------------------

    def render(self, t):
        """Render satu frame (wajib diimplementasikan subclass). t = waktu (ms)."""
        raise NotImplementedError

    # ----------------------------------------------------------------
    # Helper: Spawn Paket Baru
    # ----------------------------------------------------------------

    def spawn_packet(
        self, sx, sy, dx, dy,
        cx=None, cy=None,
        color=COLOR_RR, label="",
        speed=0.008, on_arrive=None, radius=10,
    ) -> Packet:
        """Buat paket baru yang bergerak dari (sx,sy) ke (dx,dy)."""
        if cx is None: cx = (sx + dx) / 2
        if cy is None: cy = (sy + dy) / 2
        p = Packet(sx=sx, sy=sy, dx=dx, dy=dy, cx=cx, cy=cy,
                   color=color, label=label, speed=speed,
                   on_arrive=on_arrive, radius=radius)
        self.packets.append(p)
        return p
