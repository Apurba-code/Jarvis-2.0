import sys
import os
import psutil
import math
import random
import time
import threading
from datetime import datetime
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

import traceback

def custom_excepthook(type, value, tb):
    print("UNCAUGHT EXCEPTION:", type, value, sys.stderr)
    traceback.print_exception(type, value, tb)

sys.excepthook = custom_excepthook


# =============================================================================
# DESIGN TOKENS
# =============================================================================
COLOR_BG = "#030406"
COLOR_ION_CYAN = "#00F6FF"
COLOR_ELECTRIC_BLUE = "#29B6FF"
COLOR_WARM_AMBER = "#FFB347"
COLOR_EMERGENCY_RED = "#FF3B3B"
COLOR_TEXT = "#EAFBFF"
COLOR_SUBTEXT = "#668899"

# Helper for safe gradient color stops
def safe_set_color_at(grad, pos, color):
    clamped_pos = max(0.01, min(0.99, float(pos)))
    grad.setColorAt(clamped_pos, color)

# Helper for smooth Catmull-Rom to Cubic Bezier spline generation
def build_spline_path(points):
    path = QPainterPath()
    if not points:
        return path
    path.moveTo(points[0])
    if len(points) < 2:
        return path
    if len(points) == 2:
        path.lineTo(points[1])
        return path
    
    n = len(points)
    for i in range(n - 1):
        p0 = points[max(0, i - 1)]
        p1 = points[i]
        p2 = points[i + 1]
        p3 = points[min(n - 1, i + 2)]
        
        dx = (p2.x() - p1.x()) / 3.0
        cp1_y = p1.y() + (p2.y() - p0.y()) / 6.0
        cp2_y = p2.y() - (p3.y() - p1.y()) / 6.0
        
        cp1 = QPointF(p1.x() + dx, cp1_y)
        cp2 = QPointF(p2.x() - dx, cp2_y)
        
        path.cubicTo(cp1, cp2, p2)
    return path


# =============================================================================
# BACKGROUND CANVAS (Multi-Layer Depth, Holographic Dust, Blueprint Grid & Rings)
# =============================================================================
class BackgroundCanvas(QWidget):
    """Cinematic background with 3 particle depth layers, orbiting dust, blueprint markings & edge-faded scan beam"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        
        # 3 Particle Depth Layers (Background, Midground, Foreground)
        self.particles_bg = []
        for _ in range(35):
            self.particles_bg.append({
                'x': random.uniform(0, 1920),
                'y': random.uniform(0, 1080),
                'size': random.uniform(0.8, 1.4),
                'speed_y': random.uniform(-0.15, -0.05),
                'speed_x': random.uniform(-0.08, 0.08),
                'alpha': random.uniform(20, 60),
                'pulse_speed': random.uniform(0.01, 0.03)
            })
            
        self.particles_mid = []
        for _ in range(25):
            self.particles_mid.append({
                'x': random.uniform(0, 1920),
                'y': random.uniform(0, 1080),
                'size': random.uniform(1.5, 2.5),
                'speed_y': random.uniform(-0.35, -0.1),
                'speed_x': random.uniform(-0.15, 0.15),
                'alpha': random.uniform(50, 130),
                'pulse_speed': random.uniform(0.02, 0.04)
            })
            
        self.particles_fg = []
        for _ in range(15):
            self.particles_fg.append({
                'x': random.uniform(0, 1920),
                'y': random.uniform(0, 1080),
                'size': random.uniform(2.8, 4.0),
                'speed_y': random.uniform(-0.6, -0.2),
                'speed_x': random.uniform(-0.25, 0.25),
                'alpha': random.uniform(90, 180),
                'pulse_speed': random.uniform(0.03, 0.06)
            })

        # Holographic Orbital Dust Particles around Center
        self.holo_dust = []
        for _ in range(30):
            self.holo_dust.append({
                'radius': random.uniform(120, 500),
                'angle': random.uniform(0, math.pi * 2),
                'speed': random.uniform(0.001, 0.004),
                'size': random.uniform(1.0, 2.0),
                'alpha': random.uniform(30, 90)
            })
            
        self.grid_offset = 0.0
        self.scan_beam_y = 0.0
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._animate_bg)
        self.timer.start(16)  # 60 FPS
        
    def _animate_bg(self):
        w = self.width() or 1920
        h = self.height() or 1080
        
        self.grid_offset = (self.grid_offset + 0.15) % 40
        self.scan_beam_y = (self.scan_beam_y + 1.4) % (h + 300)
        
        t = time.time()
        
        # Update Depth Particles
        for layer in (self.particles_bg, self.particles_mid, self.particles_fg):
            for p in layer:
                p['y'] += p['speed_y']
                p['x'] += p['speed_x']
                p['current_alpha'] = int(p['alpha'] + math.sin(t * p['pulse_speed'] * 8) * (p['alpha'] * 0.3))
                
                if p['y'] < -10:
                    p['y'] = h + 10
                    p['x'] = random.uniform(0, w)
                if p['x'] < -10:
                    p['x'] = w + 10
                elif p['x'] > w + 10:
                    p['x'] = -10
                    
        # Update Orbital Holographic Dust
        for d in self.holo_dust:
            d['angle'] += d['speed']
            
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        rect = self.rect()
        w, h = rect.width(), rect.height()
        center = QPointF(w / 2.0, h / 2.0)
        
        # 1. Deep Matte Black Base Fill
        painter.fillRect(rect, QColor(COLOR_BG))
        
        # 2. Volumetric Radial Atmosphere Fog
        fog_grad = QRadialGradient(center, w * 0.55)
        safe_set_color_at(fog_grad, 0.0, QColor(0, 246, 255, 16))
        safe_set_color_at(fog_grad, 0.45, QColor(0, 180, 255, 6))
        safe_set_color_at(fog_grad, 1.0, QColor(3, 4, 6, 0))
        painter.fillRect(rect, fog_grad)
        
        # 3. Faint Circular Guide Rings around Central HUD
        ring_pen = QPen(QColor(0, 246, 255, 10), 0.8, Qt.DashLine)
        painter.setPen(ring_pen)
        painter.setBrush(Qt.NoBrush)
        for r in (340, 540, 740):
            painter.drawEllipse(center, r, r)
            
        # 4. Animated Blueprint Grid & Crosshair Intersections
        grid_pen = QPen(QColor(0, 246, 255, 10), 0.7, Qt.DotLine)
        painter.setPen(grid_pen)
        
        grid_size = 40
        x_start = 0
        while x_start < w:
            painter.drawLine(int(x_start), 0, int(x_start), h)
            x_start += grid_size
            
        y_start = self.grid_offset
        while y_start < h:
            painter.drawLine(0, int(y_start), w, int(y_start))
            y_start += grid_size
            
        # Subtle Intersection Crosses ('+') every 160px
        cross_pen = QPen(QColor(0, 246, 255, 25), 0.9)
        painter.setPen(cross_pen)
        for cx_idx in range(160, w, 160):
            for cy_idx in range(160, h, 160):
                painter.drawLine(cx_idx - 4, cy_idx, cx_idx + 4, cy_idx)
                painter.drawLine(cx_idx, cy_idx - 4, cx_idx, cy_idx + 4)
                
        # 5. Blueprint Blueprint & Telemetry Watermark Markings
        font_bp = QFont("Consolas", 7)
        painter.setFont(font_bp)
        painter.setPen(QColor(0, 246, 255, 40))
        painter.drawText(40, 45, "LAT 40.7128° N // LON 74.0060° W")
        painter.drawText(w - 220, 45, "SYS_GRID // SECTOR 04-A")
        painter.drawText(40, h - 35, "HUD_ORBITAL_FRAMEWORK // v2.0")
        painter.drawText(w - 220, h - 35, "AI_CORE_FREQUENCY // 60.0 HZ")
        
        # 6. Render Layered Particles (Background -> Midground -> Foreground)
        for layer in (self.particles_bg, self.particles_mid, self.particles_fg):
            for p in layer:
                a = max(0, min(255, p.get('current_alpha', 50)))
                painter.setPen(Qt.NoPen)
                painter.setBrush(QColor(0, 246, 255, a))
                painter.drawEllipse(QPointF(p['x'], p['y']), p['size'], p['size'])
                
        # 7. Orbiting Holographic Dust
        for d in self.holo_dust:
            dx = center.x() + math.cos(d['angle']) * d['radius']
            dy = center.y() + math.sin(d['angle']) * d['radius']
            painter.setPen(Qt.NoPen)
            painter.setBrush(QColor(0, 246, 255, int(d['alpha'])))
            painter.drawEllipse(QPointF(dx, dy), d['size'], d['size'])

        # 8. Volumetric Scan Beam with Edge Fading & Soft Bloom
        if self.scan_beam_y < h + 150:
            beam_y = self.scan_beam_y - 100
            beam_rect = QRectF(0, beam_y, w, 100)
            
            beam_grad = QLinearGradient(0, beam_y, 0, beam_y + 100)
            safe_set_color_at(beam_grad, 0.0, QColor(0, 246, 255, 0))
            safe_set_color_at(beam_grad, 0.5, QColor(0, 246, 255, 14))
            safe_set_color_at(beam_grad, 1.0, QColor(0, 246, 255, 0))
            
            painter.fillRect(beam_rect, beam_grad)
            
            # Faint edge mask gradient for beam ends
            edge_mask = QLinearGradient(0, 0, w, 0)
            safe_set_color_at(edge_mask, 0.0, QColor(3, 4, 6, 200))
            safe_set_color_at(edge_mask, 0.15, QColor(3, 4, 6, 0))
            safe_set_color_at(edge_mask, 0.85, QColor(3, 4, 6, 0))
            safe_set_color_at(edge_mask, 1.0, QColor(3, 4, 6, 200))
            painter.fillRect(beam_rect, edge_mask)


# =============================================================================
# BASE GLASS PANEL (Symmetrical 190px Cards with Illuminated Corner Brackets)
# =============================================================================
class GlassPanel(QFrame):
    """Base holographic glass container with symmetrical layout, fixed typography & soft corner brackets"""
    def __init__(self, title="MODULE", parent=None):
        super().__init__(parent)
        self.title = title
        self.setFixedHeight(220)
        self.glow_phase = random.uniform(0, math.pi * 2)
        
        # Micro-glow phase timer
        self.glow_timer = QTimer(self)
        self.glow_timer.timeout.connect(self._update_glow)
        self.glow_timer.start(50)
        
    def _update_glow(self):
        self.glow_phase += 0.04
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        rect = self.rect().adjusted(2, 2, -2, -2)
        rx, ry, rw, rh = rect.x(), rect.y(), rect.width(), rect.height()
        
        # 1. Glass Panel Translucent Fill
        path = QPainterPath()
        path.addRoundedRect(QRectF(rect), 10, 10)
        
        grad = QLinearGradient(rect.topLeft(), rect.bottomRight())
        safe_set_color_at(grad, 0.0, QColor(0, 246, 255, 10))
        safe_set_color_at(grad, 0.5, QColor(0, 150, 255, 4))
        safe_set_color_at(grad, 1.0, QColor(3, 4, 6, 20))
        painter.fillPath(path, grad)
        
        # 2. Soft Reduced-Brightness Border
        border_alpha = int(20 + math.sin(self.glow_phase) * 8)
        painter.setPen(QPen(QColor(0, 246, 255, border_alpha), 0.8))
        painter.drawRoundedRect(QRectF(rect), 10, 10)
        
        # 3. Illuminated Corner Brackets (Brighter vertices with soft edges)
        bracket_pen = QPen(QColor(COLOR_ION_CYAN), 1.4)
        painter.setPen(bracket_pen)
        b_len = 10
        
        # Top-Left Bracket
        painter.drawLine(rx, ry + b_len, rx, ry)
        painter.drawLine(rx, ry, rx + b_len, ry)
        # Top-Right Bracket
        painter.drawLine(rx + rw - b_len, ry, rx + rw, ry)
        painter.drawLine(rx + rw, ry, rx + rw, ry + b_len)
        # Bottom-Left Bracket
        painter.drawLine(rx, ry + rh - b_len, rx, ry + rh)
        painter.drawLine(rx, ry + rh, rx + b_len, ry + rh)
        # Bottom-Right Bracket
        painter.drawLine(rx + rw - b_len, ry + rh, rx + rw, ry + rh)
        painter.drawLine(rx + rw, ry + rh, rx + rw, ry + rh - b_len)
        
        # Corner Vertex Illumination Dots
        dot_pen = QPen(QColor(COLOR_ION_CYAN), 2.5)
        painter.setPen(dot_pen)
        painter.drawPoint(rx, ry)
        painter.drawPoint(rx + rw, ry)
        painter.drawPoint(rx, ry + rh)
        painter.drawPoint(rx + rw, ry + rh)
        
        # 4. Title Header (Fixed Letter-Spacing, Completely Stable)
        if self.title:
            font = QFont("Consolas", 8, QFont.Bold)
            font.setLetterSpacing(QFont.AbsoluteSpacing, 1.5)
            painter.setFont(font)
            painter.setPen(QColor(COLOR_ION_CYAN))
            painter.drawText(rect.adjusted(14, 10, -14, 0), Qt.AlignLeft | Qt.AlignTop, self.title)
            
            # Status Indicator Dot (Top Right)
            painter.setPen(Qt.NoPen)
            painter.setBrush(QColor(COLOR_ION_CYAN))
            painter.drawEllipse(QPointF(rx + rw - 14, ry + 14), 2.5, 2.5)


# =============================================================================
# LEFT PANEL 1 — CPU INTELLIGENCE (Smooth Spline Curve Graph)
# =============================================================================
class CpuModule(GlassPanel):
    """Panel 1: CPU usage with smooth Bezier spline graph and glow fill"""
    def __init__(self, parent=None):
        super().__init__("SYSTEM // CPU INTELLIGENCE", parent)
        self.history = [18.0] * 40
        self.target_val = 18.0
        self.curr_val = 18.0
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._poll)
        self.timer.start(800)

    def _poll(self):
        try:
            val = float(psutil.cpu_percent())
        except:
            val = random.uniform(14, 42)
        self.target_val = val
        self.history.pop(0)
        self.history.append(self.target_val)
        self.update()

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        rect = self.rect().adjusted(14, 32, -14, -12)
        
        # Telemetry Metrics (Fixed Letter Spacing)
        cpu_val = self.history[-1]
        freq = "3.8 GHz"
        threads = "16 THREADS"
        temp = f"{int(40 + cpu_val * 0.32)}°C"
        
        font = QFont("Consolas", 8)
        font.setLetterSpacing(QFont.AbsoluteSpacing, 1.0)
        painter.setFont(font)
        
        painter.setPen(QColor(COLOR_TEXT))
        painter.drawText(rect.x(), rect.y() + 14, f"USAGE: {cpu_val:.1f}%")
        
        painter.setPen(QColor(COLOR_SUBTEXT))
        painter.drawText(rect.x() + 120, rect.y() + 14, f"TEMP: {temp}")
        painter.drawText(rect.x(), rect.y() + 28, f"FREQ: {freq}")
        painter.drawText(rect.x() + 120, rect.y() + 28, f"CORE: {threads}")
        
        # Smooth Spline Curve Graph Area
        graph_rect = QRectF(rect.x(), rect.y() + 40, rect.width(), rect.height() - 40)
        
        step = graph_rect.width() / (len(self.history) - 1)
        h = graph_rect.height()
        
        points = []
        for i, val in enumerate(self.history):
            x = graph_rect.x() + i * step
            y = graph_rect.y() + h - (val / 100.0 * (h - 8)) - 4
            points.append(QPointF(x, y))
            
        spline_path = build_spline_path(points)
        
        # Gradient Fill Under Spline Graph
        fill_path = QPainterPath(spline_path)
        fill_path.lineTo(graph_rect.x() + graph_rect.width(), graph_rect.y() + h)
        fill_path.lineTo(graph_rect.x(), graph_rect.y() + h)
        fill_path.closeSubpath()
        
        fill_grad = QLinearGradient(graph_rect.topLeft(), graph_rect.bottomLeft())
        safe_set_color_at(fill_grad, 0.0, QColor(0, 246, 255, 35))
        safe_set_color_at(fill_grad, 1.0, QColor(0, 246, 255, 0))
        painter.fillPath(fill_path, fill_grad)
        
        # Dual-Layer Spline Curve (Glow + Core Line)
        painter.setPen(QPen(QColor(0, 246, 255, 60), 3.0))
        painter.drawPath(spline_path)
        
        painter.setPen(QPen(QColor(COLOR_ION_CYAN), 1.2))
        painter.drawPath(spline_path)


# =============================================================================
# LEFT PANEL 2 — MEMORY (Glass Chamber & Liquid Sine Wave)
# =============================================================================
class MemoryModule(GlassPanel):
    """Panel 2: Glass liquid visualization for RAM"""
    def __init__(self, parent=None):
        super().__init__("MEMORY // CACHE & LIQUID", parent)
        self.mem_pct = 42.0
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._poll)
        self.timer.start(1000)

    def _poll(self):
        try:
            v = psutil.virtual_memory()
            self.mem_pct = float(v.percent)
        except:
            self.mem_pct = random.uniform(38, 52)
        self.update()

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        rect = self.rect().adjusted(14, 32, -14, -12)
        
        font = QFont("Consolas", 8)
        font.setLetterSpacing(QFont.AbsoluteSpacing, 1.0)
        painter.setFont(font)
        
        painter.setPen(QColor(COLOR_TEXT))
        painter.drawText(rect.x(), rect.y() + 14, f"USED: {self.mem_pct:.1f}%")
        
        total_gb = 16.0
        avail_gb = total_gb * (1.0 - self.mem_pct / 100.0)
        cached_gb = total_gb * 0.22
        
        painter.setPen(QColor(COLOR_SUBTEXT))
        painter.drawText(rect.x() + 120, rect.y() + 14, f"FREE: {avail_gb:.1f} GB")
        painter.drawText(rect.x(), rect.y() + 28, f"CACHE: {cached_gb:.1f} GB")
        
        # Liquid Chamber Box
        box_rect = QRectF(rect.x(), rect.y() + 38, rect.width(), rect.height() - 38)
        
        painter.setPen(QPen(QColor(0, 246, 255, 30), 0.8))
        painter.setBrush(QColor(0, 246, 255, 5))
        painter.drawRoundedRect(box_rect, 6, 6)
        
        # Liquid Surface Sine Wave
        fill_h = (self.mem_pct / 100.0) * box_rect.height()
        t = time.time() * 3.0
        
        liq_path = QPainterPath()
        liq_path.moveTo(box_rect.x(), box_rect.y() + box_rect.height() - fill_h)
        
        step = 4
        w_curr = 0
        while w_curr <= box_rect.width():
            wave = math.sin((w_curr / box_rect.width() * 6) + t) * 2.0
            liq_path.lineTo(box_rect.x() + w_curr, box_rect.y() + box_rect.height() - fill_h + wave)
            w_curr += step
            
        liq_path.lineTo(box_rect.x() + box_rect.width(), box_rect.y() + box_rect.height())
        liq_path.lineTo(box_rect.x(), box_rect.y() + box_rect.height())
        liq_path.closeSubpath()
        
        grad = QLinearGradient(box_rect.topLeft(), box_rect.bottomLeft())
        safe_set_color_at(grad, 0.0, QColor(0, 246, 255, 60))
        safe_set_color_at(grad, 1.0, QColor(0, 120, 255, 15))
        painter.fillPath(liq_path, grad)
        
        # Wave Crest Line
        surf_path = QPainterPath()
        surf_path.moveTo(box_rect.x(), box_rect.y() + box_rect.height() - fill_h)
        w_curr = 0
        while w_curr <= box_rect.width():
            wave = math.sin((w_curr / box_rect.width() * 6) + t) * 2.0
            surf_path.lineTo(box_rect.x() + w_curr, box_rect.y() + box_rect.height() - fill_h + wave)
            w_curr += step
            
        painter.setPen(QPen(QColor(COLOR_ION_CYAN), 1.2))
        painter.drawPath(surf_path)


# =============================================================================
# LEFT PANEL 3 — STORAGE (SSD Disk Matrix Ring)
# =============================================================================
class StorageModule(GlassPanel):
    """Panel 3: Segmented disk ring visualization"""
    def __init__(self, parent=None):
        super().__init__("STORAGE // SSD DISK MATRIX", parent)
        self.rot_angle = 0.0
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._rotate)
        self.timer.start(30)

    def _rotate(self):
        self.rot_angle = (self.rot_angle + 0.6) % 360
        self.update()

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        rect = self.rect().adjusted(14, 32, -14, -12)
        
        ring_center = QPointF(rect.x() + 55, rect.y() + 68)
        r_outer = 40
        r_inner = 28
        
        painter.save()
        painter.translate(ring_center)
        
        # Orbiting ticks
        painter.save()
        painter.rotate(self.rot_angle)
        painter.setPen(QPen(QColor(0, 246, 255, 60), 0.8))
        for i in range(12):
            painter.rotate(30)
            painter.drawLine(r_outer + 3, 0, r_outer + 6, 0)
        painter.restore()
        
        # Disk Arcs
        segments = 16
        used_segs = 11
        for i in range(segments):
            angle_start = i * (360 / segments) + 4
            angle_span = (360 / segments) - 8
            
            c = QColor(COLOR_ION_CYAN) if i < used_segs else QColor(0, 246, 255, 25)
            pen = QPen(c, 6)
            pen.setCapStyle(Qt.FlatCap)
            painter.setPen(pen)
            
            arc_r = (r_outer + r_inner) / 2
            arc_rect = QRectF(-arc_r, -arc_r, arc_r * 2, arc_r * 2)
            painter.drawArc(arc_rect, int(angle_start * 16), int(angle_span * 16))
            
        painter.restore()
        
        # Text Telemetry Metrics
        tx = rect.x() + 125
        ty = rect.y() + 25
        
        font = QFont("Consolas", 8, QFont.Bold)
        font.setLetterSpacing(QFont.AbsoluteSpacing, 1.0)
        painter.setFont(font)
        painter.setPen(QColor(COLOR_TEXT))
        painter.drawText(tx, ty, "DRIVE: SSD NVMe")
        
        font.setWeight(QFont.Normal)
        painter.setFont(font)
        painter.setPen(QColor(COLOR_SUBTEXT))
        painter.drawText(tx, ty + 18, "FREE: 412 GB / 1 TB")
        painter.drawText(tx, ty + 34, "READ: 3.2 GB/s")
        painter.drawText(tx, ty + 50, "WRITE: 2.8 GB/s")
        
        # Usage Bar
        painter.setPen(QPen(QColor(0, 246, 255, 40), 0.8))
        painter.drawRect(tx, ty + 62, 120, 5)
        painter.fillRect(QRectF(tx, ty + 62, 84, 5), QColor(COLOR_ION_CYAN))


# =============================================================================
# MAIN AI CORE (Dominant +18% Size, 256 Living Radial Spikes & Concentric Rings)
# =============================================================================
class JarvisCoreHUD(QWidget):
    """Central AI Core (dominant visual HUD core) with 256 organic audio-reactive spikes & concentric holographic rings"""
    NUM_SPIKES = 256

    def __init__(self, parent=None):
        super().__init__(parent)
        self.state = "IDLE"
        # Minimum floor prevents collapse; sizeHint guides layout to allocate ~520px
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setMinimumSize(300, 300)

        # Multi-Ring Orbit Angles
        self.ring_outer = 0.0
        self.ring_mid = 0.0
        self.ring_inner = 0.0
        self.spectrum_rot = 0.0
        self.pulse = 0.0
        self.scan_y = 0.0

        # 256 Spikes Data
        self.spike_heights = [4.0] * self.NUM_SPIKES
        self.target_heights = [4.0] * self.NUM_SPIKES
        self.spike_phases = [random.uniform(0, math.pi * 2) for _ in range(self.NUM_SPIKES)]
        self.audio_bars = [0.0] * 24
        self.audio_phase = 0.0

        # Speech audio pumping
        self._speaking = False
        self._speech_thread = None

        # Core Particles
        self.core_particles = []
        for _ in range(25):
            self.core_particles.append({
                'r': random.uniform(15, 125),
                'angle': random.uniform(0, math.pi * 2),
                'speed': random.uniform(0.008, 0.025),
                'size': random.uniform(1.0, 2.5)
            })

        self.anim_timer = QTimer(self)
        self.anim_timer.timeout.connect(self._animate)
        self.anim_timer.start(16)  # 60 FPS

    def notify_speech_start(self, audio_file=None):
        """Called just before TTS playback starts. Spawns audio-pump thread."""
        self.state = "SPEAKING"
        self._speaking = True
        self._speech_thread = threading.Thread(
            target=self._pump_speech_audio,
            args=(audio_file,),
            daemon=True
        )
        self._speech_thread.start()

    def _pump_speech_audio(self, audio_file):
        """
        Zero-delay procedural pump — starts immediately when speech begins.
        Drives audio_bars and spike animation with high dynamic range while Jarvis speaks.
        """
        import pygame
        num_bars = len(self.audio_bars)
        fps = 60
        t0 = time.time()

        # Wait up to 1.2s for pygame mixer music to start playing
        wait_start = time.time()
        while time.time() - wait_start < 1.2:
            try:
                if pygame.mixer.get_init() and pygame.mixer.music.get_busy():
                    break
            except Exception:
                pass
            time.sleep(0.02)

        while self._speaking:
            try:
                # Stop if pygame playback has finished after initial start window
                if (time.time() - t0 > 0.5) and pygame.mixer.get_init() and not pygame.mixer.music.get_busy():
                    break

                t = time.time() - t0

                # High-energy multi-frequency wave composition for speech cadence
                base_amp = (
                    math.sin(t * 7.5) * 0.35 +
                    math.sin(t * 14.2) * 0.25 +
                    math.sin(t * 22.8) * 0.20 +
                    random.uniform(0.15, 0.40)
                )
                base_amp = max(0.25, min(1.0, base_amp))

                # Update all audio bars with wide individual variations
                for b in range(num_bars):
                    offset = math.sin(t * 12.0 + b * 0.75) * 0.35
                    self.audio_bars[b] = max(0.1, min(1.0, base_amp + offset))

            except Exception:
                pass
            time.sleep(1.0 / fps)

        # Smooth fade-out after speech ends
        for _ in range(25):
            for b in range(num_bars):
                self.audio_bars[b] *= 0.80
            time.sleep(0.016)

        self._speaking = False

    def sizeHint(self):
        return QSize(520, 520)




    def _animate(self):
        t = time.time()
        
        # Multi-Ring Speeds
        r_speed = 0.5 if self.state == "IDLE" else (2.0 if self.state == "THINKING" else 1.4)
        
        self.ring_outer = (self.ring_outer - r_speed * 0.4) % 360
        self.ring_mid = (self.ring_mid + r_speed * 0.9) % 360
        self.ring_inner = (self.ring_inner - r_speed * 1.5) % 360
        
        self.pulse = (math.sin(t * 2.2) + 1.0) / 2.0
        self.scan_y = (self.scan_y + 1.5) % (self.height() + 150)
        
        # Spectrum Slow Rotation (~50s per 360 deg turn during idle)
        rot_step = 0.12 if self.state == "IDLE" else (0.18 if self.state == "LISTENING" else 0.26)
        self.spectrum_rot = (self.spectrum_rot + rot_step) % 360.0
        
        # Core Floating Particles
        for p in self.core_particles:
            p['angle'] += p['speed']
            
        # Compute 256 Organic / Audio Spike Targets
        num = self.NUM_SPIKES
        self.audio_phase += 0.12
        
        for i in range(num):
            frac = i / num
            phi = self.spike_phases[i]
            
            if self.state == "IDLE":
                # Organic multi-frequency breathing so heights are never uniform
                wave_a = math.sin(t * 0.75 + frac * math.pi * 2) * 0.30
                wave_b = math.sin(t * 1.85 + frac * math.pi * 4 + phi) * 0.25
                wave_c = math.sin(t * 4.20 + phi * 2.0) * 0.12
                norm = (wave_a + wave_b + wave_c + 0.67) / 1.34
                target = 4.0 + norm * 11.0  # 4–15 px
                
            elif self.state == "LISTENING":
                mic_amp = max(0.0, min(1.0, self.audio_bars[0]))
                wave_a = math.sin(t * 2.5 + frac * math.pi * 4 + phi) * 0.35
                wave_b = math.sin(t * 5.0 - frac * math.pi * 2) * 0.15
                base_h = 4.0 + ((wave_a + wave_b + 0.50) / 1.00) * 10.0
                target = base_h + mic_amp * 26.0  # 4–40 px
                
            elif self.state == "THINKING":
                wave_a = math.sin(t * 2.2 - frac * math.pi * 6) * 0.40
                wave_b = math.sin(t * 1.5 + frac * math.pi * 6) * 0.20
                wave_c = math.sin(t * 3.8 + phi) * 0.08
                norm = (wave_a + wave_b + wave_c + 0.68) / 1.36
                target = 4.0 + norm * 16.0  # 4–20 px
                
            else:  # SPEAKING
                bar_idx = int(i * len(self.audio_bars) / num) % len(self.audio_bars)
                amp = max(0.0, min(1.0, self.audio_bars[bar_idx]))
                wave_a = math.sin(self.audio_phase + frac * math.pi * 4 + phi) * 0.20
                wave_b = math.sin(self.audio_phase * 0.6 - frac * math.pi * 2) * 0.10
                base_h = 4.0 + ((wave_a + wave_b + 0.30) / 0.60) * 8.0
                target = base_h + amp * 60.0  # 4–72 px
                
            self.target_heights[i] = max(2.0, target)
            
        # Lerp Interpolation
        lerp_k = 0.06 if self.state == "IDLE" else (0.10 if self.state == "THINKING" else (0.14 if self.state == "LISTENING" else 0.18))
        for i in range(num):
            self.spike_heights[i] += lerp_k * (self.target_heights[i] - self.spike_heights[i])
            
        if self.state != "SPEAKING":
            for i in range(len(self.audio_bars)):
                self.audio_bars[i] *= 0.82
                
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        center = self.rect().center()
        cx, cy = center.x(), center.y()
        
        color = QColor(COLOR_WARM_AMBER) if self.state in ("LISTENING", "SPEAKING") else QColor(COLOR_ION_CYAN)
        cr, cg, cb = color.red(), color.green(), color.blue()
        
        # 1. Outer Volumetric Atmosphere Glow
        glow_intensity = 60 if self.state == "SPEAKING" else (40 if self.state != "IDLE" else 22)
        grad = QRadialGradient(center, 250)
        safe_set_color_at(grad, 0.0, QColor(cr, cg, cb, int(glow_intensity + self.pulse * 12)))
        safe_set_color_at(grad, 0.75, QColor(cr, cg, cb, 4))
        safe_set_color_at(grad, 1.0, QColor(0, 0, 0, 0))
        painter.fillRect(self.rect(), grad)
        
        # 2. Vertical Connection Line extending to Status section at bottom
        beam_pen = QPen(QColor(cr, cg, cb, int(40 + self.pulse * 30)), 1.2, Qt.DashLine)
        painter.setPen(beam_pen)
        painter.drawLine(int(cx), int(cy + 225), int(cx), self.height())
        
        painter.translate(center)
        
        # 3. Layer 1: Outer Dashed Guide Ring (r=240)
        painter.save()
        painter.rotate(self.ring_outer)
        painter.setPen(QPen(QColor(cr, cg, cb, 30), 0.8, Qt.DashLine))
        painter.drawEllipse(QRectF(-240, -240, 480, 480))
        painter.restore()
        
        # 4. Layer 2: Cardinal Compass Degree Ring (r=220)
        painter.save()
        painter.rotate(self.ring_mid)
        painter.setPen(QPen(QColor(cr, cg, cb, 50), 1.0))
        painter.drawArc(QRectF(-220, -220, 440, 440), 0, 100 * 16)
        painter.drawArc(QRectF(-220, -220, 440, 440), 130 * 16, 200 * 16)
        
        # Degree Ticks & Crosshairs
        for i in range(8):
            painter.rotate(45)
            painter.drawLine(210, 0, 225, 0)
        painter.restore()
        
        # 5. Layer 3: Coordinate Micro-Tick Ring (r=190)
        painter.save()
        painter.rotate(self.ring_inner)
        painter.setPen(QPen(QColor(cr, cg, cb, 65), 0.8))
        painter.drawEllipse(QRectF(-190, -190, 380, 380))
        for _ in range(12):
            painter.rotate(30)
            painter.drawLine(182, 0, 190, 0)
        painter.restore()
        
        # 6. Living 256 Radial Spikes Spectrum (r=188)
        self._draw_256_spikes(painter, color)
        
        # 7. Floating Inner Core Particles
        for p in self.core_particles:
            px = math.cos(p['angle']) * p['r']
            py = math.sin(p['angle']) * p['r']
            painter.setPen(Qt.NoPen)
            painter.setBrush(QColor(cr, cg, cb, 140))
            painter.drawEllipse(QPointF(px, py), p['size'], p['size'])
            
        # 8. Inner Holographic Orb & Stable Core Branding
        orb_grad = QRadialGradient(QPointF(0, 0), 130)
        safe_set_color_at(orb_grad, 0.0, QColor(cr, cg, cb, 50))
        safe_set_color_at(orb_grad, 0.7, QColor(cr, cg, cb, 12))
        safe_set_color_at(orb_grad, 1.0, QColor(0, 0, 0, 0))
        painter.setBrush(orb_grad)
        painter.setPen(QPen(QColor(cr, cg, cb, 90), 1.0))
        painter.drawEllipse(QRectF(-130, -130, 260, 260))
        
        # Core Branding Text (Fixed Letter-Spacing, Completely Stable)
        font_core = QFont("Consolas", 20, QFont.Bold)
        font_core.setLetterSpacing(QFont.AbsoluteSpacing, 4.0)
        painter.setFont(font_core)
        painter.setPen(color)
        painter.drawText(QRectF(-110, -35, 220, 40), Qt.AlignCenter, "JARVIS")
        
        font_sub = QFont("Consolas", 8)
        font_sub.setLetterSpacing(QFont.AbsoluteSpacing, 2.5)
        painter.setFont(font_sub)
        painter.setPen(QColor(COLOR_TEXT))
        painter.drawText(QRectF(-110, 12, 220, 20), Qt.AlignCenter, "SYSTEM // ONLINE")

    def _draw_256_spikes(self, painter, color):
        num = self.NUM_SPIKES
        ring_r = 188
        cr, cg, cb = color.red(), color.green(), color.blue()
        max_h = 15.0 if self.state == "IDLE" else (20.0 if self.state == "THINKING" else (40.0 if self.state == "LISTENING" else 72.0))
        
        for i in range(num):
            h = self.spike_heights[i]
            if h < 0.5:
                continue
                
            total_rad = math.radians(i * (360.0 / num) + self.spectrum_rot)
            cos_a = math.cos(total_rad)
            sin_a = math.sin(total_rad)
            
            sx = cos_a * ring_r
            sy = sin_a * ring_r
            ex = cos_a * (ring_r + h)
            ey = sin_a * (ring_r + h)
            
            norm_h = min(1.0, h / max_h)
            base_alpha = int(75 + norm_h * 180)
            
            # Glow Pass
            glow_pen = QPen(QColor(cr, cg, cb, int(base_alpha * 0.22)), 1.2 + norm_h * 2.6)
            glow_pen.setCapStyle(Qt.RoundCap)
            painter.setPen(glow_pen)
            painter.drawLine(QPointF(sx, sy), QPointF(ex, ey))
            
            # Core Line Pass
            core_pen = QPen(QColor(cr, cg, cb, base_alpha), 0.8 + norm_h * 1.0)
            core_pen.setCapStyle(Qt.RoundCap)
            painter.setPen(core_pen)
            painter.drawLine(QPointF(sx, sy), QPointF(ex, ey))


# =============================================================================
# RIGHT PANEL 1 — CLOCK & DATE (Fixed Letter-Spacing)
# =============================================================================
class ClockModule(GlassPanel):
    """Panel 1 (Right): Digital Clock & Date with fixed letter-spacing"""
    def __init__(self, parent=None):
        super().__init__("CHRONO // SYSTEM TIME", parent)
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update)
        self.timer.start(1000)

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        rect = self.rect().adjusted(14, 32, -14, -12)
        now = datetime.now()
        
        time_str = now.strftime("%H:%M:%S")
        date_str = now.strftime("%A // %d %B %Y").upper()
        
        # Digital Clock (Fixed Letter Spacing)
        font_clock = QFont("Consolas", 26, QFont.Bold)
        font_clock.setLetterSpacing(QFont.AbsoluteSpacing, 2.5)
        painter.setFont(font_clock)
        painter.setPen(QColor(COLOR_ION_CYAN))
        painter.drawText(rect.x(), rect.y() + 48, time_str)
        
        # Date Text
        font_date = QFont("Consolas", 8)
        font_date.setLetterSpacing(QFont.AbsoluteSpacing, 1.5)
        painter.setFont(font_date)
        painter.setPen(QColor(COLOR_SUBTEXT))
        painter.drawText(rect.x(), rect.y() + 78, date_str)


# =============================================================================
# RIGHT PANEL 2 — WEATHER (Holographic Line-Art Vector Icon)
# =============================================================================
class WeatherModule(GlassPanel):
    """Panel 2 (Right): Weather metrics with pure holographic line-art vector icon"""
    def __init__(self, parent=None):
        super().__init__("ATMOSPHERE // WEATHER METRICS", parent)
        self.cloud_phase = 0.0
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._animate_cloud)
        self.timer.start(50)

    def _animate_cloud(self):
        self.cloud_phase = (self.cloud_phase + 0.04) % (math.pi * 2)
        self.update()

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        rect = self.rect().adjusted(14, 32, -14, -12)
        
        # Holographic Line-Art Weather Icon
        icon_center = QPointF(rect.x() + 45, rect.y() + 52)
        
        # 1. Holographic Wireframe Sun Rays
        painter.save()
        painter.translate(icon_center)
        painter.setPen(QPen(QColor(COLOR_WARM_AMBER), 1.2))
        for _ in range(8):
            painter.rotate(45)
            painter.drawLine(15, 0, 22, 0)
        painter.restore()
        
        # Sun Line-Art Core Ring
        painter.setPen(QPen(QColor(COLOR_WARM_AMBER), 1.2))
        painter.setBrush(Qt.NoBrush)
        painter.drawEllipse(icon_center, 10, 10)
        
        # Faint Isobar Circles around Sun
        painter.setPen(QPen(QColor(0, 246, 255, 25), 0.8, Qt.DashLine))
        painter.drawEllipse(icon_center, 28, 28)
        
        # 2. Holographic Vector Cloud Outline (Line-Art)
        cx = icon_center.x() + math.sin(self.cloud_phase) * 1.8
        cy = icon_center.y() + 8
        
        cloud_path = QPainterPath()
        cloud_path.addEllipse(QPointF(cx - 8, cy), 10, 9)
        cloud_path.addEllipse(QPointF(cx + 4, cy - 4), 12, 11)
        cloud_path.addEllipse(QPointF(cx + 14, cy), 9, 8)
        
        # Translucent Fill + Crisp Cyan Line-Art Stroke
        painter.setBrush(QColor(0, 246, 255, 12))
        painter.setPen(QPen(QColor(COLOR_ION_CYAN), 1.2))
        painter.drawPath(cloud_path)
        
        # Text Metrics
        tx = rect.x() + 115
        ty = rect.y() + 22
        
        font = QFont("Consolas", 13, QFont.Bold)
        font.setLetterSpacing(QFont.AbsoluteSpacing, 1.0)
        painter.setFont(font)
        painter.setPen(QColor(COLOR_TEXT))
        painter.drawText(tx, ty, "24°C // CLEAR")
        
        font.setWeight(QFont.Normal)
        font.setPointSize(8)
        painter.setFont(font)
        painter.setPen(QColor(COLOR_SUBTEXT))
        painter.drawText(tx, ty + 20, "HUMIDITY: 58%")
        painter.drawText(tx, ty + 36, "WIND: 12 km/h NW")
        painter.drawText(tx, ty + 52, "LOCATION: NEW YORK // AR")


# =============================================================================
# RIGHT PANEL 3 — VOICE OSCILLOSCOPE
# =============================================================================
class VoiceOscilloscopeModule(GlassPanel):
    """Panel 3 (Right): Voice activity oscilloscope waveform"""
    def __init__(self, parent=None):
        super().__init__("AUDIO // VOICE ACTIVITY OSCILLOSCOPE", parent)
        self.phase = 0.0
        self.is_active = False
        self.mic_level = 0.0
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._tick)
        self.timer.start(16)

    def set_level(self, lvl):
        self.mic_level = lvl
        self.is_active = lvl > 0.05

    def _tick(self):
        self.phase += 0.12
        self.update()

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        rect = self.rect().adjusted(14, 35, -14, -12)
        
        box = QRectF(rect.x(), rect.y() + 10, rect.width(), rect.height() - 10)
        painter.setPen(QPen(QColor(0, 246, 255, 25), 0.8))
        painter.setBrush(QColor(0, 246, 255, 4))
        painter.drawRoundedRect(box, 6, 6)
        
        cy = box.y() + box.height() / 2.0
        painter.setPen(QPen(QColor(0, 246, 255, 35), 0.8, Qt.DashLine))
        painter.drawLine(QPointF(box.x(), cy), QPointF(box.x() + box.width(), cy))
        
        # Waveform Spline
        path = QPainterPath()
        path.moveTo(box.x(), cy)
        
        step = 3
        w_curr = 0
        amp = (self.mic_level * (box.height() * 0.42)) if self.is_active else 2.2
        
        while w_curr <= box.width():
            norm_x = w_curr / box.width()
            env = math.sin(norm_x * math.pi)
            
            wave1 = math.sin(norm_x * 14 + self.phase) * amp * env
            wave2 = math.sin(norm_x * 28 - self.phase * 1.5) * (amp * 0.35) * env
            noise = random.uniform(-0.6, 0.6)
            
            y = cy + wave1 + wave2 + noise
            path.lineTo(box.x() + w_curr, y)
            w_curr += step
            
        color = QColor(COLOR_WARM_AMBER) if self.is_active else QColor(COLOR_ION_CYAN)
        painter.setPen(QPen(color, 1.3))
        painter.drawPath(path)


# =============================================================================
# BOTTOM STATUS BAR
# =============================================================================
# =============================================================================
# MIC TOGGLE BUTTON (Holographic animated microphone)
# =============================================================================
class MicToggleButton(QWidget):
    """Holographic pulsing mic button — click to toggle listening on/off"""
    toggled = pyqtSignal(bool)  # True = mic ON / listening

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(64, 64)
        self.setCursor(Qt.PointingHandCursor)
        self._active = True          # starts ON
        self._pulse = 0.0
        self._hover = False
        self._ring_angle = 0.0

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._animate)
        self._timer.start(16)        # 60 FPS

    # ── state ──────────────────────────────────────────────────────────────
    @property
    def active(self):
        return self._active

    def set_active(self, val: bool):
        self._active = val
        self.update()

    # ── animation ──────────────────────────────────────────────────────────
    def _animate(self):
        self._pulse = (self._pulse + 0.07) % (math.pi * 2)
        if self._active:
            self._ring_angle = (self._ring_angle + 1.8) % 360
        self.update()

    # ── interaction ────────────────────────────────────────────────────────
    def enterEvent(self, event):
        self._hover = True
        self.update()

    def leaveEvent(self, event):
        self._hover = False
        self.update()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._active = not self._active
            self.toggled.emit(self._active)
            self.update()

    # ── paint ──────────────────────────────────────────────────────────────
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        cx, cy = w / 2.0, h / 2.0

        pulse_scale = 1.0 + (math.sin(self._pulse) * 0.06 if self._active else 0)
        btn_r = 26 * pulse_scale

        if self._active:
            # Outer pulsing glow ring
            glow_a = int(40 + math.sin(self._pulse) * 20)
            glow_r = btn_r + 6 + math.sin(self._pulse) * 3
            glow_grad = QRadialGradient(QPointF(cx, cy), glow_r + 4)
            glow_grad.setColorAt(0.0, QColor(0, 246, 255, glow_a))
            glow_grad.setColorAt(1.0, QColor(0, 246, 255, 0))
            painter.setBrush(glow_grad)
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(QPointF(cx, cy), glow_r + 4, glow_r + 4)

            # Orbiting arc (active state indicator)
            painter.save()
            painter.translate(cx, cy)
            painter.rotate(self._ring_angle)
            arc_pen = QPen(QColor(0, 246, 255, 130), 1.4)
            arc_pen.setCapStyle(Qt.RoundCap)
            painter.setPen(arc_pen)
            painter.drawArc(QRectF(-btn_r - 6, -btn_r - 6, (btn_r + 6) * 2, (btn_r + 6) * 2),
                            0, 120 * 16)
            painter.drawArc(QRectF(-btn_r - 6, -btn_r - 6, (btn_r + 6) * 2, (btn_r + 6) * 2),
                            160 * 16, 80 * 16)
            painter.restore()

            fill_color = QColor(0, 246, 255, 220 if self._hover else 180)
            icon_color = QColor(3, 4, 6)
        else:
            # Dim inactive style
            fill_color = QColor(60, 80, 90, 200 if self._hover else 150)
            icon_color = QColor(100, 130, 140)

        # Button circle
        circle_grad = QRadialGradient(QPointF(cx, cy - 4), btn_r)
        r, g, b = fill_color.red(), fill_color.green(), fill_color.blue()
        circle_grad.setColorAt(0.0, QColor(r, g, b, min(255, fill_color.alpha() + 40)))
        circle_grad.setColorAt(1.0, fill_color)
        painter.setBrush(circle_grad)
        border_col = QColor(0, 246, 255, 200) if self._active else QColor(80, 100, 110, 180)
        painter.setPen(QPen(border_col, 1.5))
        painter.drawEllipse(QPointF(cx, cy), btn_r, btn_r)

        # Mic icon (drawn with lines)
        painter.setPen(QPen(icon_color, 2.0, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        mic_w, mic_h = 8, 12
        mic_x, mic_y = cx - mic_w / 2, cy - mic_h / 2 - 2
        # Capsule body
        mic_path = QPainterPath()
        mic_path.addRoundedRect(QRectF(mic_x, mic_y, mic_w, mic_h), mic_w / 2, mic_w / 2)
        painter.setBrush(icon_color)
        painter.drawPath(mic_path)

        # Stand arc
        painter.setBrush(Qt.NoBrush)
        stand_rect = QRectF(cx - 7, cy + 1, 14, 9)
        painter.drawArc(stand_rect, 0, -180 * 16)
        # Stem
        painter.drawLine(int(cx), int(cy + 10), int(cx), int(cy + 14))
        # Base bar
        painter.drawLine(int(cx - 5), int(cy + 14), int(cx + 5), int(cy + 14))

        # Strike-through line when muted
        if not self._active:
            mute_pen = QPen(QColor(255, 80, 80, 220), 2.2, Qt.SolidLine, Qt.RoundCap)
            painter.setPen(mute_pen)
            painter.drawLine(int(cx - 14), int(cy - 14), int(cx + 14), int(cy + 14))


class BottomStatusBar(QFrame):
    """Floating Holographic Status Bar spanning across the bottom"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(42)
        self._mic_active = True   # tracks mic state for live badge update

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update)
        self.timer.start(1000)

    def set_mic_active(self, active: bool):
        self._mic_active = active
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        rect = self.rect().adjusted(2, 2, -2, -2)

        path = QPainterPath()
        path.addRoundedRect(QRectF(rect), 8, 8)

        grad = QLinearGradient(rect.topLeft(), rect.bottomRight())
        safe_set_color_at(grad, 0.0, QColor(0, 246, 255, 12))
        safe_set_color_at(grad, 1.0, QColor(0, 100, 200, 6))
        painter.fillPath(path, grad)

        painter.setPen(QPen(QColor(0, 246, 255, 35), 0.8))
        painter.drawRoundedRect(QRectF(rect), 8, 8)

        mic_val = "ACTIVE" if self._mic_active else "MUTED"
        badgelist = [
            ("NET", "1.2 Gbps"),
            ("GPU", f"{random.randint(28, 42)}%"),
            ("INET", "ONLINE"),
            ("BAT", "100% [AC]"),
            ("MIC", mic_val),
            ("SPK", "78%"),
            ("MODEL", "JARVIS v2.0"),
            ("FPS", "60"),
            ("LATENCY", "12 ms")
        ]

        font = QFont("Consolas", 8)
        font.setLetterSpacing(QFont.AbsoluteSpacing, 1.0)
        painter.setFont(font)

        total_w = rect.width()
        spacing = total_w / len(badgelist)

        for i, (label, val) in enumerate(badgelist):
            cx = i * spacing + spacing / 2.0

            painter.setPen(QColor(COLOR_SUBTEXT))
            painter.drawText(int(cx - 45), int(rect.height() / 2 + 4), f"{label}:")

            # MIC badge turns red when muted
            if label == "MIC" and not self._mic_active:
                painter.setPen(QColor(COLOR_EMERGENCY_RED))
            else:
                painter.setPen(QColor(COLOR_ION_CYAN))
            painter.drawText(int(cx - 10), int(rect.height() / 2 + 4), val)

            if i < len(badgelist) - 1:
                painter.setPen(QPen(QColor(0, 246, 255, 25), 0.8))
                painter.drawLine(int((i + 1) * spacing), 10, int((i + 1) * spacing), rect.height() - 10)


# =============================================================================
# MAIN WINDOW DASHBOARD (JARVIS HUD)
# =============================================================================
class JarvisHUD(QMainWindow):
    chat_signal = pyqtSignal(str, str)
    status_signal = pyqtSignal(str)
    mic_signal = pyqtSignal(bool)   # True = mic ON, False = mic OFF / muted
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("JARVIS // NEXT-GEN HOLOGRAPHIC HUD")
        self.resize(1920, 1080)
        self.setWindowFlags(Qt.Window)
        self.setStyleSheet(f"QMainWindow {{ background-color: {COLOR_BG}; }}")
        
        # Background Canvas
        self.bg_canvas = BackgroundCanvas(self)
        
        # Central Layout Container
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(12, 18, 12, 15)
        main_layout.setSpacing(15)

        # =====================================================================
        # Fully proportional 5-zone layout — scales to ANY window size / DPI
        # Stretch ratios:  [Left 19] [Gutter 3] [Center 52] [Gutter 3] [Right 19]  = 96 units total
        # =====================================================================

        # === LEFT COLUMN (stretch=24, max 480px) ===
        left_col = QWidget()
        left_col.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        left_col.setMaximumWidth(480)
        left_layout = QVBoxLayout(left_col)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(0)

        self.cpu_panel = CpuModule()
        self.mem_panel = MemoryModule()
        self.storage_panel = StorageModule()

        # Space-between vertical distribution
        left_layout.addWidget(self.cpu_panel)
        left_layout.addStretch(1)
        left_layout.addWidget(self.mem_panel)
        left_layout.addStretch(1)
        left_layout.addWidget(self.storage_panel)

        # === CENTER COLUMN (stretch=48) ===
        center_col = QWidget()
        center_col.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        center_layout = QVBoxLayout(center_col)
        center_layout.setContentsMargins(0, 0, 0, 0)
        center_layout.setAlignment(Qt.AlignCenter)

        self.core_hud = JarvisCoreHUD()

        # Status Label Below Core Sphere (Fixed Letter-Spacing, Completely Stable)
        self.status_label = QLabel("STATUS // STANDBY")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet(f"""
            color: {COLOR_ION_CYAN};
            font-family: Consolas;
            font-size: 18px;
            font-weight: bold;
            letter-spacing: 3px;
            margin-top: 10px;
            background: transparent;
        """)

        # Mic toggle button
        self.mic_btn = MicToggleButton()
        self.mic_btn.toggled.connect(self._on_mic_toggled)

        center_layout.addStretch()
        center_layout.addWidget(self.core_hud, 0, Qt.AlignCenter)
        center_layout.addWidget(self.status_label, 0, Qt.AlignCenter)
        center_layout.addSpacing(10)
        center_layout.addWidget(self.mic_btn, 0, Qt.AlignCenter)
        center_layout.addStretch()

        # === RIGHT COLUMN (stretch=24, max 480px — mirror of left) ===
        right_col = QWidget()
        right_col.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        right_col.setMaximumWidth(480)
        right_layout = QVBoxLayout(right_col)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)

        self.clock_panel = ClockModule()
        self.weather_panel = WeatherModule()
        self.oscilloscope_panel = VoiceOscilloscopeModule()

        # Space-between vertical distribution
        right_layout.addWidget(self.clock_panel)
        right_layout.addStretch(1)
        right_layout.addWidget(self.weather_panel)
        right_layout.addStretch(1)
        right_layout.addWidget(self.oscilloscope_panel)

        # === ASSEMBLE with proportional stretch factors ===
        self.grid_layout = QHBoxLayout()
        self.grid_layout.setSpacing(0)
        self.grid_layout.setContentsMargins(0, 0, 0, 0)
        self.grid_layout.addWidget(left_col,   24)   # ~24%
        self.grid_layout.addStretch(2)               # ~2% left gutter
        self.grid_layout.addWidget(center_col, 48)   # ~48%
        self.grid_layout.addStretch(2)               # ~2% right gutter
        self.grid_layout.addWidget(right_col,  24)   # ~24%
        
        # Build Main Stack
        main_layout.addLayout(self.grid_layout, 1)
        
        # Connected Signals
        self.status_signal.connect(self._handle_status)
        self.chat_signal.connect(self._handle_chat)
        self.mic_signal.connect(self._handle_mic)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.bg_canvas.setGeometry(self.rect())

    def get_mic_active(self) -> bool:
        """Thread-safe read of current mic toggle state."""
        return self.mic_btn.active

    def update_status(self, status):
        self.status_signal.emit(status)

    def set_transcription(self, text):
        self.chat_signal.emit("USER", text)

    def set_response(self, text):
        self.chat_signal.emit("JARVIS", text)

    def log_event(self, text):
        self.chat_signal.emit("SYSTEM", text)

    def set_audio_level(self, level, source="mic"):
        if source == "mic":
            self.oscilloscope_panel.set_level(level)
            self.core_hud.audio_bars[0] = min(1.0, level * 2.0)

    @pyqtSlot(str)
    def _handle_status(self, status):
        self.status_label.setText(f"STATUS // {status}")
        self.core_hud.state = status
        
        color = COLOR_WARM_AMBER if status in ("LISTENING", "SPEAKING") else COLOR_ION_CYAN
        self.status_label.setStyleSheet(f"""
            color: {color};
            font-family: Consolas;
            font-size: 18px;
            font-weight: bold;
            letter-spacing: 3px;
            margin-top: 10px;
            background: transparent;
        """)

    @pyqtSlot(bool)
    def _handle_mic(self, active: bool):
        """React to mic toggle — update status label."""
        if not active:
            # Immediately reflect muted state in status
            self.status_label.setText("STATUS // IDLE")
            self.core_hud.state = "IDLE"
            self.status_label.setStyleSheet(f"""
                color: {COLOR_ION_CYAN};
                font-family: Consolas;
                font-size: 18px;
                font-weight: bold;
                letter-spacing: 3px;
                margin-top: 10px;
                background: transparent;
            """)

    def _on_mic_toggled(self, active: bool):
        """Slot wired to MicToggleButton.toggled — bridges to thread-safe signal."""
        self.mic_signal.emit(active)

    @pyqtSlot(str, str)
    def _handle_chat(self, sender, msg):
        pass


JarvisUI = JarvisHUD

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = JarvisHUD()
    window.show()
    sys.exit(app.exec_())

