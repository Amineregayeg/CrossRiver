import pygame
import sys
import math
import random
import os

pygame.init()

# ================================================================
# AUDIO SETUP
# ================================================================
try:
    pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
    AUDIO_AVAILABLE = True
except Exception:
    AUDIO_AVAILABLE = False

SOUND_PATH = os.path.join(os.path.dirname(__file__), "assets", "sounds")


def load_sound(filename):
    if not AUDIO_AVAILABLE:
        return None
    path = os.path.join(SOUND_PATH, filename)
    if os.path.exists(path):
        try:
            return pygame.mixer.Sound(path)
        except Exception as e:
            print(f"Could not load sound {path}: {e}")
    return None


def play_sound(sound, volume=1.0):
    if sound is not None:
        try:
            sound.set_volume(volume)
            sound.play()
        except Exception:
            pass


# Load sounds
ambience_sound = load_sound("forest_ambience.wav")
wind_sfx = load_sound("wind_gust.wav")
crash_sfx = load_sound("crash.wav")

# Load multiple paddle splash variants for variety
_paddle_variants = []
for _fname in ["paddle_splash.wav", "paddle_splash2.wav", "paddle_splash3.wav"]:
    _s = load_sound(_fname)
    if _s:
        _paddle_variants.append(_s)
# Load bubble overlay sounds
_bubble_variants = []
for _fname in ["paddle_bubble.ogg", "paddle_bubble2.ogg"]:
    _s = load_sound(_fname)
    if _s:
        _bubble_variants.append(_s)
# Fallback: if no variants loaded, keep None
paddle_sfx = _paddle_variants[0] if _paddle_variants else None


def play_paddle_sound(volume=0.1):
    """Play a random paddle splash variant + optional bubble overlay."""
    if _paddle_variants:
        snd = random.choice(_paddle_variants)
        play_sound(snd, volume)
    if _bubble_variants and random.random() < 0.5:
        bub = random.choice(_bubble_variants)
        play_sound(bub, volume * 0.3)


# Start ambience loop
if ambience_sound:
    try:
        ambience_sound.play(loops=-1)
        ambience_sound.set_volume(0.3)
    except Exception:
        pass

# Start background music (uses pygame.mixer.music for streaming)
if AUDIO_AVAILABLE:
    _music_path = os.path.join(SOUND_PATH, "background_music.ogg")
    if os.path.exists(_music_path):
        try:
            pygame.mixer.music.load(_music_path)
            pygame.mixer.music.set_volume(0.15)
            pygame.mixer.music.play(loops=-1)
        except Exception as e:
            print(f"Could not load background music: {e}")

# ================================================================
# WINDOW SETUP
# ================================================================
WIDTH, HEIGHT = 1250, 650
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Cross River")
clock = pygame.time.Clock()
font = pygame.font.Font(None, 72)
title_font = pygame.font.Font(None, 110)
subtitle_font = pygame.font.Font(None, 32)
button_font = pygame.font.Font(None, 48)
hud_font = pygame.font.Font(None, 36)

ASSET_PATH = os.path.join(os.path.dirname(__file__), "assets", "images")


# ================================================================
# ASSET LOADING
# ================================================================
def load_image(subdir, filename, size=None):
    path = os.path.join(ASSET_PATH, subdir, filename)
    if not os.path.exists(path):
        print(f"Asset not found: {path}")
        return None
    try:
        img = pygame.image.load(path).convert_alpha()
        if size:
            img = pygame.transform.scale(img, size)
        return img
    except Exception as e:
        print(f"Error loading {path}: {e}")
        return None


tree_canopy1 = load_image("obstacles", "forest1-removebg-preview.png")
tree_canopy2 = load_image("obstacles", "forest2-removebg-preview.png")
forest_floor = load_image("obstacles", "forest_tile.png")


# ================================================================
# WATER ANIMATION SYSTEM
# ================================================================
class WaterRenderer:
    """Animated river water with layered waves, flow particles, and sparkles."""

    def __init__(self, w, h):
        self.w, self.h = w, h

        # Deterministic sparkle positions
        rng = random.Random(123)
        self.sparkles = [
            (rng.randint(0, w), rng.randint(0, h), rng.uniform(0, 6.28))
            for _ in range(70)
        ]

        # Flow particles (show current direction)
        rng2 = random.Random(456)
        self.flow_particles = []
        for _ in range(45):
            self.flow_particles.append({
                "x": rng2.uniform(0, w),
                "y": rng2.uniform(0, h),
                "speed": rng2.uniform(18, 40),
                "length": rng2.randint(12, 35),
                "phase": rng2.uniform(0, 6.28),
            })

    def draw(self, screen, dt, time, camera_y=0):
        # Deep water base
        screen.fill((22, 52, 138))

        # Wave layer 1: Broad gentle swells
        phase1 = time * 0.7
        for y in range(0, self.h, 16):
            y_world = y + camera_y
            pts = []
            for x in range(0, self.w + 8, 8):
                wy = y + math.sin(x * 0.009 + phase1 + y_world * 0.003) * 5
                pts.append((x, int(wy)))
            if len(pts) > 1:
                pygame.draw.lines(screen, (35, 72, 175), False, pts, 3)

        # Wave layer 2: Medium ripples flowing in the opposite direction
        phase2 = time * -0.45
        for y in range(4, self.h, 22):
            y_world = y + camera_y
            pts = []
            for x in range(0, self.w + 10, 10):
                wy = y + math.sin(x * 0.014 + phase2 + y_world * 0.005) * 3.5
                pts.append((x, int(wy)))
            if len(pts) > 1:
                pygame.draw.lines(screen, (48, 92, 198), False, pts, 2)

        # Wave layer 3: Fine shimmering detail
        phase3 = time * 0.9
        for y in range(8, self.h, 30):
            y_world = y + camera_y
            pts = []
            for x in range(0, self.w + 12, 12):
                wy = (
                    y
                    + math.sin(x * 0.006 + phase3 + y_world * 0.001) * 7
                    + math.sin(x * 0.02 + phase3 * 0.6 + y_world * 0.001) * 2
                )
                pts.append((x, int(wy)))
            if len(pts) > 1:
                pygame.draw.lines(screen, (60, 112, 215), False, pts, 2)

        # Wave layer 4: Highlight accent waves
        phase4 = time * 0.35
        for y in range(2, self.h, 38):
            y_world = y + camera_y
            pts = []
            for x in range(0, self.w + 10, 10):
                wy = y + math.sin(x * 0.011 + phase4 + y_world * 0.002) * 4
                pts.append((x, int(wy)))
            if len(pts) > 1:
                pygame.draw.lines(screen, (72, 130, 230), False, pts, 1)

        # Flow particles (vertical current streaks)
        for p in self.flow_particles:
            p["y"] += p["speed"] * dt
            if p["y"] > self.h + 20:
                p["y"] = -p["length"]
                p["x"] = random.uniform(0, self.w)

            brightness = 0.5 + 0.5 * math.sin(time * 1.5 + p["phase"])
            if brightness > 0.4:
                c = int(55 + brightness * 30)
                x_pos, y_pos = int(p["x"]), int(p["y"])
                end_y = int(p["y"] + p["length"] * brightness)
                pygame.draw.line(
                    screen,
                    (c, min(255, c + 35), min(255, c + 75)),
                    (x_pos, y_pos),
                    (x_pos, end_y),
                    1,
                )

        # Sparkles (twinkling sun reflections)
        for sx, sy, ph in self.sparkles:
            b = math.sin(time * 2.8 + ph)
            if b > 0.55:
                intensity = (b - 0.55) / 0.45
                size = 1 + int(intensity * 2.5)
                r = min(255, int(185 + intensity * 70))
                g = min(255, int(210 + intensity * 45))
                pygame.draw.circle(screen, (r, g, 255), (sx, sy), size)


# ================================================================
# FOREST RENDERING - Pre-rendered with real tree canopy assets
# ================================================================
def create_forest_surface(cubes, w, h, floor_tile, canopy1, canopy2, cap_trees=False):
    """Pre-render forest with floor texture and top-down tree canopy assets."""
    surface = pygame.Surface((w, h), pygame.SRCALPHA)

    rng = random.Random(42)

    for cx, cy, cw, ch in cubes:
        # ---- Forest floor ----
        if floor_tile:
            tile_size = 96
            scaled_floor = pygame.transform.scale(floor_tile, (tile_size, tile_size))
            for tx in range(cx, cx + cw, tile_size):
                for ty in range(cy, cy + ch, tile_size):
                    clip_w = min(tile_size, cx + cw - tx)
                    clip_h = min(tile_size, cy + ch - ty)
                    if clip_w > 0 and clip_h > 0:
                        if clip_w >= tile_size and clip_h >= tile_size:
                            surface.blit(scaled_floor, (tx, ty))
                        else:
                            clipped = scaled_floor.subsurface(
                                (0, 0, min(clip_w, tile_size), min(clip_h, tile_size))
                            )
                            surface.blit(clipped, (tx, ty))
        else:
            pygame.draw.rect(surface, (18, 40, 15), (cx, cy, cw, ch))

        # ---- Dark undergrowth spots ----
        for _ in range(max(1, int(cw * ch / 250))):
            ux = cx + rng.randint(0, max(1, cw - 1))
            uy = cy + rng.randint(0, max(1, ch - 1))
            us = rng.randint(5, 12)
            g = rng.randint(18, 40)
            pygame.draw.circle(surface, (g - 8, g, g - 10), (ux, uy), us)

        # ---- Place tree canopies from assets ----
        available = [c for c in [canopy1, canopy2] if c is not None]

        if available:
            margin = 25
            safe_w = max(1, cw - margin * 2)
            safe_h = max(1, ch - margin * 2)
            area = safe_w * safe_h
            tree_count = max(3, int(area / 700))
            if cap_trees:
                tree_count = min(80, tree_count)

            trees = []
            for _ in range(tree_count):
                tx = cx + rng.randint(margin, max(margin + 1, cw - margin))
                ty = cy + rng.randint(margin, max(margin + 1, ch - margin))
                size = rng.randint(50, 90)
                rot = rng.choice([0, 90, 180, 270]) + rng.randint(-20, 20)
                ci = rng.randint(0, len(available) - 1)
                trees.append((tx, ty, size, rot, ci))

            trees.sort(key=lambda t: t[1])

            for tx, ty, size, rot, ci in trees:
                canopy = available[ci]
                scaled = pygame.transform.scale(canopy, (size, size))
                rotated = pygame.transform.rotate(scaled, rot)

                # Shadow (dark version, offset)
                shadow = rotated.copy()
                shadow.fill((0, 0, 0, 55), special_flags=pygame.BLEND_RGBA_MULT)
                sr = shadow.get_rect(center=(tx + 5, ty + 5))
                surface.blit(shadow, sr)

                # Canopy
                cr = rotated.get_rect(center=(tx, ty))
                surface.blit(rotated, cr)
        else:
            # Fallback: procedural trees if no assets found
            margin = 10
            area = max(1, (cw - margin * 2) * (ch - margin * 2))
            tree_count = max(2, int(area / 400))
            if cap_trees:
                tree_count = min(80, tree_count)

            trees = []
            for _ in range(tree_count):
                tx = cx + rng.randint(margin, max(margin + 1, cw - margin))
                ty = cy + rng.randint(margin, max(margin + 1, ch - margin))
                sz = rng.randint(14, 24)
                trees.append((tx, ty, sz))

            trees.sort(key=lambda t: t[1])

            for tx, ty, sz in trees:
                gv = rng.randint(-15, 15)
                pygame.draw.circle(
                    surface, (8, 18, 6), (tx + 3, ty + 3), sz + 2
                )
                pygame.draw.circle(
                    surface, (28 + gv, 85 + gv, 22 + gv), (tx, ty), sz
                )
                pygame.draw.circle(
                    surface,
                    (38 + gv, 110 + gv, 30 + gv),
                    (tx - 1, ty - 1),
                    int(sz * 0.75),
                )
                pygame.draw.circle(
                    surface,
                    (55 + gv, 145 + gv, 42 + gv),
                    (tx - sz // 4, ty - sz // 4),
                    int(sz * 0.5),
                )
                pygame.draw.circle(
                    surface,
                    (70 + gv, 170 + gv, 55 + gv),
                    (tx - sz // 3, ty - sz // 3),
                    int(sz * 0.28),
                )

    # ---- Forest edge (border where forest meets water) ----
    for cx, cy, cw, ch in cubes:
        pygame.draw.rect(surface, (10, 28, 8), (cx, cy, cw, ch), 3)

    return surface


# ================================================================
# ROCK RENDERING - Pre-rendered stone obstacles
# ================================================================
def create_rock_surface(cubes, w, h):
    """Pre-render rock obstacles as gray/brown stone shapes."""
    surface = pygame.Surface((w, h), pygame.SRCALPHA)
    rng = random.Random(314)

    for cx, cy, cw, ch in cubes:
        # Base rock fill
        pygame.draw.rect(surface, (85, 78, 68), (cx, cy, cw, ch))

        # Irregular stone texture
        num_stones = max(3, int(cw * ch / 500))
        for _ in range(num_stones):
            sx = cx + rng.randint(2, max(3, cw - 2))
            sy = cy + rng.randint(2, max(3, ch - 2))
            stone_size = rng.randint(6, 18)
            num_verts = rng.randint(5, 8)
            points = []
            for i in range(num_verts):
                ang = (i / num_verts) * math.pi * 2
                r = stone_size * rng.uniform(0.5, 1.0)
                px = max(cx, min(cx + cw, sx + math.cos(ang) * r))
                py = max(cy, min(cy + ch, sy + math.sin(ang) * r))
                points.append((int(px), int(py)))
            if len(points) >= 3:
                gray = rng.randint(55, 125)
                brown = rng.randint(0, 20)
                color = (min(255, gray + brown), min(255, gray + brown // 2), max(0, gray - brown // 2))
                pygame.draw.polygon(surface, color, points)
                highlight = tuple(min(255, c + 25) for c in color)
                pygame.draw.polygon(surface, highlight, points, 1)

        # Crack lines
        for _ in range(max(1, int(cw * ch / 1500))):
            lx1 = cx + rng.randint(3, max(4, cw - 3))
            ly1 = cy + rng.randint(3, max(4, ch - 3))
            lx2 = max(cx, min(cx + cw, lx1 + rng.randint(-25, 25)))
            ly2 = max(cy, min(cy + ch, ly1 + rng.randint(-25, 25)))
            pygame.draw.line(surface, (45, 40, 35), (lx1, ly1), (lx2, ly2), 1)

        # Dark border
        pygame.draw.rect(surface, (40, 35, 30), (cx, cy, cw, ch), 2)

    return surface


# ================================================================
# SHORELINE FOAM (animated dots at water-forest boundary)
# ================================================================
def precompute_foam(cubes, w, h):
    pts = []
    rng = random.Random(789)
    for cx, cy, cw, ch in cubes:
        # Top edge
        for x in range(cx, cx + cw, 10):
            if 0 <= cy - 4 <= h:
                pts.append((x, cy - 4, rng.uniform(0, 6.28)))
        # Bottom edge
        for x in range(cx, cx + cw, 10):
            if 0 <= cy + ch + 4 <= h:
                pts.append((x, cy + ch + 4, rng.uniform(0, 6.28)))
        # Left edge
        for y in range(cy, cy + ch, 10):
            if 0 <= cx - 4 <= w:
                pts.append((cx - 4, y, rng.uniform(0, 6.28)))
        # Right edge
        for y in range(cy, cy + ch, 10):
            if 0 <= cx + cw + 4 <= w:
                pts.append((cx + cw + 4, y, rng.uniform(0, 6.28)))
    return [(x, y, p) for x, y, p in pts if 0 <= x <= w and 0 <= y <= h]


def draw_foam(screen, foam_pts, time, camera_y=0):
    for fx, fy, phase in foam_pts:
        sy = fy - camera_y
        if sy < -10 or sy > HEIGHT + 10:
            continue
        b = 0.5 + 0.5 * math.sin(time * 1.8 + phase)
        if b > 0.45:
            c = min(255, int(90 + b * 110))
            size = 1 + int(b * 1.5)
            pygame.draw.circle(screen, (c, min(255, c + 25), 255), (int(fx), int(sy)), size)


# ================================================================
# OAR (RAMP) ANIMATION
# ================================================================
class OarAnimator:
    """Animates left and right oar rowing strokes."""

    def __init__(self):
        self.left_angle = 0.0
        self.right_angle = 0.0
        self.left_time = -1.0
        self.right_time = -1.0
        self.stroke_duration = 0.35
        self.max_sweep = 40

        self.left_splash = 0.0
        self.right_splash = 0.0

    def trigger_left(self):
        self.left_time = 0.0
        self.left_splash = 1.0

    def trigger_right(self):
        self.right_time = 0.0
        self.right_splash = 1.0

    def update(self, dt):
        if self.left_time >= 0:
            self.left_time += dt
            if self.left_time >= self.stroke_duration:
                self.left_time = -1.0
                self.left_angle = 0.0
            else:
                p = self.left_time / self.stroke_duration
                self.left_angle = math.sin(p * math.pi) * self.max_sweep

        if self.right_time >= 0:
            self.right_time += dt
            if self.right_time >= self.stroke_duration:
                self.right_time = -1.0
                self.right_angle = 0.0
            else:
                p = self.right_time / self.stroke_duration
                self.right_angle = math.sin(p * math.pi) * self.max_sweep

        self.left_splash = max(0, self.left_splash - dt * 3.5)
        self.right_splash = max(0, self.right_splash - dt * 3.5)


# ================================================================
# BOAT RENDERING (hull + deck + animated oars)
# ================================================================
def draw_boat(surface, pos, angle, oar_anim, speed=0):
    """Draw a detailed top-down boat with animated oar ramps."""

    # ---- Hull (outer shell) ----
    hull = [
        pygame.Vector2(0, -22),
        pygame.Vector2(4, -18),
        pygame.Vector2(8, -10),
        pygame.Vector2(10, 0),
        pygame.Vector2(10, 10),
        pygame.Vector2(8, 18),
        pygame.Vector2(4, 20),
        pygame.Vector2(0, 21),
        pygame.Vector2(-4, 20),
        pygame.Vector2(-8, 18),
        pygame.Vector2(-10, 10),
        pygame.Vector2(-10, 0),
        pygame.Vector2(-8, -10),
        pygame.Vector2(-4, -18),
    ]
    rot_hull = [pos + p.rotate(angle) for p in hull]

    # Shadow under boat
    shadow_off = pygame.Vector2(3, 3)
    pygame.draw.polygon(surface, (12, 25, 70), [p + shadow_off for p in rot_hull])

    # Hull base (dark wood)
    pygame.draw.polygon(surface, (110, 68, 28), rot_hull)
    pygame.draw.polygon(surface, (75, 45, 15), rot_hull, 2)

    # ---- Deck (lighter inner area) ----
    deck = [
        pygame.Vector2(0, -18),
        pygame.Vector2(3, -15),
        pygame.Vector2(6, -8),
        pygame.Vector2(7, 0),
        pygame.Vector2(7, 9),
        pygame.Vector2(6, 16),
        pygame.Vector2(3, 18),
        pygame.Vector2(0, 19),
        pygame.Vector2(-3, 18),
        pygame.Vector2(-6, 16),
        pygame.Vector2(-7, 9),
        pygame.Vector2(-7, 0),
        pygame.Vector2(-6, -8),
        pygame.Vector2(-3, -15),
    ]
    rot_deck = [pos + p.rotate(angle) for p in deck]
    pygame.draw.polygon(surface, (155, 105, 50), rot_deck)

    # Deck planks (cross lines)
    for plank_y in range(-14, 18, 4):
        p1 = pos + pygame.Vector2(-5, plank_y).rotate(angle)
        p2 = pos + pygame.Vector2(5, plank_y).rotate(angle)
        pygame.draw.line(
            surface,
            (125, 82, 35),
            (int(p1.x), int(p1.y)),
            (int(p2.x), int(p2.y)),
            1,
        )

    # Center plank (lengthwise)
    p1 = pos + pygame.Vector2(0, -16).rotate(angle)
    p2 = pos + pygame.Vector2(0, 17).rotate(angle)
    pygame.draw.line(
        surface, (130, 85, 38), (int(p1.x), int(p1.y)), (int(p2.x), int(p2.y)), 1
    )

    # Bow decoration
    bow = pos + pygame.Vector2(0, -22).rotate(angle)
    pygame.draw.circle(surface, (90, 55, 18), (int(bow.x), int(bow.y)), 3)
    pygame.draw.circle(surface, (145, 100, 42), (int(bow.x), int(bow.y)), 2)

    # ---- OARS (Ramps) ----
    for side in ("left", "right"):
        if side == "left":
            pivot_local = pygame.Vector2(-10, 4)
            sweep = oar_anim.left_angle
            extend = -1
            splash_val = oar_anim.left_splash
        else:
            pivot_local = pygame.Vector2(10, 4)
            sweep = oar_anim.right_angle
            extend = 1
            splash_val = oar_anim.right_splash

        pivot = pos + pivot_local.rotate(angle)

        # Oar direction: perpendicular to boat + animated sweep
        oar_ang = angle + extend * (90 + sweep)
        oar_dir = pygame.Vector2(0, -1).rotate(oar_ang)

        # Handle (inside boat)
        handle = pivot - oar_dir * 5
        # Shaft end
        shaft = pivot + oar_dir * 18

        # Draw shaft
        pygame.draw.line(
            surface,
            (100, 65, 22),
            (int(handle.x), int(handle.y)),
            (int(shaft.x), int(shaft.y)),
            3,
        )

        # Paddle blade at end of shaft
        paddle_end = shaft + oar_dir * 7
        perp = pygame.Vector2(oar_dir.y, -oar_dir.x)

        blade = [
            shaft + perp * 4,
            shaft - perp * 4,
            paddle_end - perp * 2.5,
            paddle_end + perp * 2.5,
        ]
        blade_int = [(int(p.x), int(p.y)) for p in blade]
        pygame.draw.polygon(surface, (125, 80, 32), blade_int)
        pygame.draw.polygon(surface, (85, 52, 18), blade_int, 1)

        # Oar lock at pivot
        pygame.draw.circle(surface, (70, 45, 15), (int(pivot.x), int(pivot.y)), 3)
        pygame.draw.circle(surface, (50, 30, 10), (int(pivot.x), int(pivot.y)), 3, 1)

        # Splash ring when oar dips
        if splash_val > 0.1:
            sp = paddle_end
            sz = int(5 + splash_val * 10)
            sc = (
                min(255, int(140 + splash_val * 115)),
                min(255, int(185 + splash_val * 70)),
                255,
            )
            pygame.draw.circle(surface, sc, (int(sp.x), int(sp.y)), sz, 1)
            if splash_val > 0.4:
                pygame.draw.circle(
                    surface, sc, (int(sp.x), int(sp.y)), sz + 5, 1
                )


# ================================================================
# WAKE EFFECT (trailing foam behind boat)
# ================================================================
class WakeSystem:
    def __init__(self):
        self.trail = []
        self.spawn_timer = 0

    def update(self, dt, boat_pos, boat_angle, speed):
        self.trail = [(x, y, a + dt) for x, y, a in self.trail if a + dt < 1.0]

        self.spawn_timer += dt
        if speed > 0.5 and self.spawn_timer > 0.04:
            self.spawn_timer = 0
            back = pygame.Vector2(0, 1).rotate(boat_angle)
            right = pygame.Vector2(1, 0).rotate(boat_angle)
            stern = boat_pos + back * 20
            spread = min(1.0, speed / 5.0)

            for s in (-1, 1):
                px = stern.x + right.x * s * (4 + spread * 3)
                py = stern.y + right.y * s * (4 + spread * 3)
                self.trail.append((px, py, 0))

    def draw(self, screen, camera_y=0):
        for px, py, age in self.trail:
            sy = py - camera_y
            if sy < -20 or sy > HEIGHT + 20:
                continue
            progress = age / 1.0
            size = max(1, int(3 * (1 - progress * 0.7)))
            brightness = int(180 * (1 - progress))
            if brightness > 25:
                c = (
                    min(255, 80 + brightness // 2),
                    min(255, 120 + brightness // 2),
                    255,
                )
                pygame.draw.circle(screen, c, (int(px), int(sy)), size)

    def clear(self):
        self.trail = []
        self.spawn_timer = 0


# ================================================================
# PARTICLE SYSTEM (for splash effects)
# ================================================================
class ParticleSystem:
    """General purpose particle system with gravity and fading."""

    def __init__(self):
        # Each particle: [x, y, vx, vy, life, max_life, color, size]
        self.particles = []

    def emit_splash(self, x, y, count):
        for _ in range(count):
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(30, 120)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed
            life = random.uniform(0.3, 0.8)
            color = (
                random.randint(150, 220),
                random.randint(200, 240),
                255,
            )
            size = random.uniform(1.5, 4.0)
            self.particles.append([x, y, vx, vy, life, life, color, size])

    def update(self, dt):
        alive = []
        for p in self.particles:
            p[4] -= dt  # life
            if p[4] <= 0:
                continue
            p[3] += 150 * dt  # gravity on vy
            p[0] += p[2] * dt  # x += vx*dt
            p[1] += p[3] * dt  # y += vy*dt
            alive.append(p)
        self.particles = alive

    def draw(self, screen, camera_y=0):
        for p in self.particles:
            x, y, vx, vy, life, max_life, color, size = p
            sy = y - camera_y
            if sy < -20 or sy > HEIGHT + 20:
                continue
            alpha_ratio = max(0, life / max_life)
            r = min(255, int(color[0] * alpha_ratio))
            g = min(255, int(color[1] * alpha_ratio))
            b = min(255, int(color[2] * alpha_ratio))
            sz = max(1, int(size * alpha_ratio))
            pygame.draw.circle(screen, (r, g, b), (int(x), int(sy)), sz)


# ================================================================
# CRASH ANIMATION
# ================================================================
class CrashAnimation:
    """Boat crash: debris particles + splash rings + callback on complete."""

    def __init__(self):
        self.active = False
        self.timer = 0
        self.duration = 1.2
        self.crash_pos = pygame.Vector2(0, 0)
        self.debris = []
        self.splash_rings = []
        self.on_complete = None

    def trigger(self, pos, angle, on_complete):
        self.active = True
        self.timer = 0
        self.crash_pos = pygame.Vector2(pos.x, pos.y)
        self.on_complete = on_complete
        # Wood debris
        self.debris = []
        for _ in range(random.randint(14, 20)):
            ang = random.uniform(0, math.pi * 2)
            spd = random.uniform(80, 220)
            life = random.uniform(0.5, 1.1)
            color = random.choice([
                (139, 69, 19), (110, 68, 28), (155, 105, 50),
                (100, 65, 22), (125, 80, 32), (75, 45, 15)
            ])
            self.debris.append([
                pos.x, pos.y,
                math.cos(ang) * spd, math.sin(ang) * spd,
                random.uniform(3, 7), color, life, life
            ])
        # Splash rings
        self.splash_rings = []
        for i in range(3):
            self.splash_rings.append({
                "x": pos.x, "y": pos.y,
                "radius": 5.0, "max_radius": 35 + i * 18,
                "delay": i * 0.12, "life": 0.7, "max_life": 0.7
            })

    def update(self, dt):
        if not self.active:
            return
        self.timer += dt
        # Debris
        alive = []
        for d in self.debris:
            d[6] -= dt
            if d[6] <= 0:
                continue
            d[3] += 250 * dt  # gravity
            d[0] += d[2] * dt
            d[1] += d[3] * dt
            alive.append(d)
        self.debris = alive
        # Splash rings
        for ring in self.splash_rings:
            if ring["delay"] > 0:
                ring["delay"] -= dt
                continue
            ring["life"] -= dt
            ring["radius"] += ring["max_radius"] / ring["max_life"] * dt
        # Done?
        if self.timer >= self.duration:
            self.active = False
            if self.on_complete:
                self.on_complete()

    def draw(self, screen, camera_y=0):
        if not self.active:
            return
        for ring in self.splash_rings:
            if ring["delay"] > 0 or ring["life"] <= 0:
                continue
            alpha = max(0, ring["life"] / ring["max_life"])
            r = int(ring["radius"])
            sy = ring["y"] - camera_y
            bright = int(180 * alpha)
            c = (min(255, 100 + bright), min(255, 150 + bright // 2), 255)
            if r > 1:
                pygame.draw.circle(screen, c, (int(ring["x"]), int(sy)), r, max(1, int(3 * alpha)))
        for d in self.debris:
            x, y, vx, vy, size, color, life, max_life = d
            sy = y - camera_y
            if sy < -20 or sy > HEIGHT + 20:
                continue
            alpha = max(0, life / max_life)
            c = tuple(max(0, int(v * alpha)) for v in color)
            sz = max(1, int(size * alpha))
            pygame.draw.circle(screen, c, (int(x), int(sy)), sz)


# ================================================================
# FISH SYSTEM (small fish swimming in the river)
# ================================================================
class FishSystem:
    """Small ambient fish swimming horizontally in the river."""

    def __init__(self, map_height):
        self.fish = []
        rng = random.Random(999)
        for _ in range(25):
            x = rng.uniform(220, WIDTH - 220)
            y = rng.uniform(100, map_height - 100)
            vx = rng.choice([-1, 1]) * rng.uniform(20, 60)
            size = rng.randint(4, 8)
            r = rng.randint(140, 200)
            g = rng.randint(160, 220)
            b = rng.randint(60, 120)
            self.fish.append({
                "x": x, "y": y, "vx": vx, "size": size,
                "color": (r, g, b),
            })

    def update(self, dt):
        for f in self.fish:
            f["x"] += f["vx"] * dt
            # Bounce off river walls
            if f["x"] < 220:
                f["x"] = 220
                f["vx"] = abs(f["vx"])
            elif f["x"] > WIDTH - 220:
                f["x"] = WIDTH - 220
                f["vx"] = -abs(f["vx"])

    def draw(self, screen, camera_y=0):
        for f in self.fish:
            sy = f["y"] - camera_y
            if sy < -20 or sy > HEIGHT + 20:
                continue
            sx = int(f["x"])
            isy = int(sy)
            sz = f["size"]
            # Body ellipse
            pygame.draw.ellipse(screen, f["color"],
                                (sx - sz, isy - sz // 2, sz * 2, sz))
            # Tail triangle
            direction = 1 if f["vx"] > 0 else -1
            tail_x = sx - direction * sz
            pygame.draw.polygon(screen, f["color"], [
                (tail_x, isy),
                (tail_x - direction * sz, isy - sz // 2),
                (tail_x - direction * sz, isy + sz // 2),
            ])


# ================================================================
# SCREEN SHAKE
# ================================================================
class ScreenShake:
    """Triggers screen shake effects that decay over time."""

    def __init__(self):
        self.intensity = 0
        self.duration = 0
        self.timer = 0
        self.offset_x = 0
        self.offset_y = 0

    def trigger(self, intensity, duration):
        self.intensity = intensity
        self.duration = duration
        self.timer = duration

    def update(self, dt):
        if self.timer > 0:
            self.timer -= dt
            if self.timer <= 0:
                self.timer = 0
                self.offset_x = 0
                self.offset_y = 0
            else:
                progress = self.timer / self.duration
                current_intensity = self.intensity * progress
                self.offset_x = random.uniform(-current_intensity, current_intensity)
                self.offset_y = random.uniform(-current_intensity, current_intensity)
        else:
            self.offset_x = 0
            self.offset_y = 0


# ================================================================
# FADE TRANSITION
# ================================================================
class FadeTransition:
    """Fade to black and back, firing a callback at peak darkness."""

    def __init__(self):
        self.active = False
        self.alpha = 0
        self.fading_in = True  # True = going to black, False = coming back
        self.callback = None
        self.speed = 500  # alpha per second
        self.callback_fired = False

    def start(self, callback):
        self.active = True
        self.alpha = 0
        self.fading_in = True
        self.callback = callback
        self.callback_fired = False

    def update(self, dt):
        if not self.active:
            return
        if self.fading_in:
            self.alpha += self.speed * dt
            if self.alpha >= 255:
                self.alpha = 255
                if not self.callback_fired and self.callback:
                    self.callback()
                    self.callback_fired = True
                self.fading_in = False
        else:
            self.alpha -= self.speed * dt
            if self.alpha <= 0:
                self.alpha = 0
                self.active = False

    def draw(self, screen):
        if not self.active:
            return
        if self.alpha > 0:
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, int(min(255, max(0, self.alpha)))))
            screen.blit(overlay, (0, 0))


# ================================================================
# WIND SYSTEM (periodic gusts for Level 2)
# ================================================================
class WindSystem:
    """Periodic wind gusts that push the boat sideways."""

    def __init__(self):
        self.active = False
        self.timer = 0
        self.next_gust_in = random.uniform(4, 7)
        self.gust_duration = 0
        self.gust_timer = 0
        self.direction = 0  # -1 left, 1 right
        self.strength = 0

    def update(self, dt):
        if self.active:
            self.gust_timer += dt
            if self.gust_timer >= self.gust_duration:
                self.active = False
                self.next_gust_in = random.uniform(4, 7)
                self.timer = 0
        else:
            self.timer += dt
            if self.timer >= self.next_gust_in:
                self.active = True
                self.gust_timer = 0
                self.gust_duration = random.uniform(1.5, 3.0)
                self.direction = random.choice([-1, 1])
                self.strength = random.uniform(0.8, 1.5)

    def get_force(self):
        if not self.active:
            return pygame.Vector2(0, 0)
        # Sine ease: ramps up then down
        progress = self.gust_timer / self.gust_duration
        ease = math.sin(progress * math.pi)
        return pygame.Vector2(self.direction * self.strength * ease, 0)


# ================================================================
# RIVER CURRENT (constant downstream push for Level 2)
# ================================================================
class RiverCurrent:
    """Constant downstream push, stronger at center, weaker at edges."""

    def __init__(self, strength=30):
        self.strength = strength

    def get_force(self, boat_x):
        # Stronger at center of river (between the walls at x=200 and x=WIDTH-200)
        river_left = 200
        river_right = WIDTH - 200
        river_width = river_right - river_left
        if river_width <= 0:
            return pygame.Vector2(0, 0)
        # Normalize position to 0..1 (0=edge, 1=center)
        center = (river_left + river_right) / 2
        dist_from_center = abs(boat_x - center) / (river_width / 2)
        dist_from_center = min(1.0, dist_from_center)
        # Stronger at center: 1.0 at center, 0.3 at edges
        factor = 1.0 - 0.7 * dist_from_center
        return pygame.Vector2(0, self.strength * factor)


# ================================================================
# START MENU
# ================================================================
class Button:
    """Modern rounded button with hover/press effects."""

    def __init__(self, x, y, w, h, text, color, hover_color, text_color=(255, 255, 255)):
        self.rect = pygame.Rect(x - w // 2, y - h // 2, w, h)
        self.text = text
        self.color = color
        self.hover_color = hover_color
        self.text_color = text_color
        self.hovered = False
        self.pressed = False
        self._blend = 0.0  # smooth hover transition

    def update(self, mouse_pos, mouse_pressed, dt):
        self.hovered = self.rect.collidepoint(mouse_pos)
        target = 1.0 if self.hovered else 0.0
        speed = 8.0
        if self._blend < target:
            self._blend = min(target, self._blend + speed * dt)
        else:
            self._blend = max(target, self._blend - speed * dt)
        clicked = False
        if self.hovered and mouse_pressed:
            if not self.pressed:
                clicked = True
            self.pressed = True
        else:
            self.pressed = False
        return clicked

    def draw(self, surface):
        t = self._blend
        r = tuple(int(self.color[i] + (self.hover_color[i] - self.color[i]) * t) for i in range(3))

        # Slight scale-up on hover
        inflate = int(t * 4)
        draw_rect = self.rect.inflate(inflate * 2, inflate)

        # Shadow
        shadow_rect = draw_rect.move(0, 3)
        pygame.draw.rect(surface, (0, 0, 0, 60), shadow_rect, border_radius=12)

        # Button body
        pygame.draw.rect(surface, r, draw_rect, border_radius=12)

        # Subtle border
        border_c = tuple(min(255, c + 40) for c in r)
        pygame.draw.rect(surface, border_c, draw_rect, width=2, border_radius=12)

        # Text
        txt = button_font.render(self.text, True, self.text_color)
        txt_rect = txt.get_rect(center=draw_rect.center)
        surface.blit(txt, txt_rect)


def draw_menu(screen, water, game_time, dt, buttons, menu_boat_angle):
    """Draw the start menu screen."""

    # Animated water background
    water.draw(screen, dt, game_time)

    # Dark overlay for contrast
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 90))
    screen.blit(overlay, (0, 0))

    # Decorative boat floating gently in center
    menu_boat_pos = pygame.Vector2(WIDTH // 2, HEIGHT // 2 + 40 + math.sin(game_time * 0.8) * 6)
    menu_oar = OarAnimator()
    menu_oar.left_angle = math.sin(game_time * 2) * 15
    menu_oar.right_angle = math.sin(game_time * 2 + math.pi) * 15
    menu_oar.left_splash = 0
    menu_oar.right_splash = 0
    draw_boat(screen, menu_boat_pos, menu_boat_angle, menu_oar, 0)

    # Title glow (layered shadows for glow effect)
    title_y = 110
    title_str = "CROSS RIVER"
    for offset, alpha in [(4, 40), (2, 80)]:
        glow = title_font.render(title_str, True, (80, 160, 255))
        glow.set_alpha(alpha)
        gr = glow.get_rect(center=(WIDTH // 2 + offset, title_y + offset))
        screen.blit(glow, gr)

    # Title main text
    title_surf = title_font.render(title_str, True, (220, 240, 255))
    title_rect = title_surf.get_rect(center=(WIDTH // 2, title_y))
    screen.blit(title_surf, title_rect)

    # Subtitle
    sub_str = "Navigate the river. Avoid the forest."
    sub_surf = subtitle_font.render(sub_str, True, (160, 190, 220))
    sub_rect = sub_surf.get_rect(center=(WIDTH // 2, title_y + 55))
    screen.blit(sub_surf, sub_rect)

    # Thin separator line
    line_y = title_y + 80
    pygame.draw.line(screen, (100, 140, 200, 80), (WIDTH // 2 - 120, line_y), (WIDTH // 2 + 120, line_y), 1)

    # Buttons
    for btn in buttons:
        btn.draw(screen)

    # Footer hint
    hint = subtitle_font.render("Arrow keys to steer", True, (120, 150, 180))
    hint_r = hint.get_rect(center=(WIDTH // 2, HEIGHT - 35))
    screen.blit(hint, hint_r)


# ================================================================
# GAME SETUP
# ================================================================

# Game state
game_state = "menu"  # "menu", "playing", "level1_complete", "level2", "level2_win"

# Menu buttons
btn_play = Button(WIDTH // 2, HEIGHT // 2 + 140, 220, 55, "PLAY", (30, 100, 200), (50, 140, 255))
btn_quit = Button(WIDTH // 2, HEIGHT // 2 + 210, 220, 55, "QUIT", (60, 60, 75), (90, 90, 110))
menu_buttons = [btn_play, btn_quit]
menu_boat_angle = 0

# Fade transition
fade = FadeTransition()

# Visual systems
water = WaterRenderer(WIDTH, HEIGHT)
oar_anim = OarAnimator()
wake = WakeSystem()

# Timer
timer_seconds = 60

# Boat state
INITIAL_BOAT_POS = pygame.Vector2(WIDTH // 2, 600)
boat_pos = INITIAL_BOAT_POS.copy()
boat_velocity = pygame.Vector2(0, 0)
boat_angle = 0

# Input tracking
left_pressed = False
right_pressed = False
input_buffer = 0
input_decay_time = 0.25

# Physics constants
MAX_SPEED = 10
ROTATION_SPEED = 450
ROTATION_STEP = 25
BASE_ACCEL = 0.6
ACCEL_PER_PRESS = 0.35
BASE_FRICTION = 0.99
SIDEWAYS_FRICTION = 0.985
SIDEWAYS_DRIFT_MULT = 0.75
SINGLE_KEY_ACCEL_MULT = 0.8
SINGLE_KEY_SIDEWAYS_MULT = 0.55

# Rotation state
rotating = False
rotation_start_angle = boat_angle
rotation_direction = 0
target_angle = boat_angle
down_pressed = False

# Obstacle cubes (x, y, width, height)
left_cube_width = 200
right_cube_width = 200
cubes = [
    (0, 0, left_cube_width, HEIGHT),
    (WIDTH - right_cube_width, 0, right_cube_width, HEIGHT),
    (200, 450, 380, 200),
    (200, 330, 750, 150),
    (670, 570, 500, 300),
    (330, 0, 720, 230),
]

boat_collision_radius = 15

# Pre-render forest surface once at startup
print("Pre-rendering Level 1 forest...")
forest_surface = create_forest_surface(
    cubes, WIDTH, HEIGHT, forest_floor, tree_canopy1, tree_canopy2
)
print("Level 1 forest ready.")

# Pre-compute shoreline foam points
foam_points = precompute_foam(cubes, WIDTH, HEIGHT)

# Level 1 extra systems
l1_crash = CrashAnimation()
l1_shake = ScreenShake()
l1_frame = pygame.Surface((WIDTH, HEIGHT))
l1_complete_timer = 0


# ================================================================
# LEVEL 2 SETUP (single-screen, rocks, wind, 45s timer)
# ================================================================
LEVEL2_FINISH_Y = 40
LEVEL2_INITIAL_POS = pygame.Vector2(WIDTH // 2, 600)

# Level 2 walls are narrower (150px vs L1's 200px) for wider river
# Rock obstacles scattered in the river
level2_cubes = [
    (0, 0, 150, HEIGHT),                   # Left forest wall
    (WIDTH - 150, 0, 150, HEIGHT),          # Right forest wall
    # Rocks in the river
    (150, 500, 220, 80),                    # Bottom-left rock
    (680, 520, 260, 100),                   # Bottom-right rock
    (320, 340, 200, 75),                    # Mid-left rock
    (580, 220, 240, 70),                    # Mid-right rock
    (820, 350, 180, 85),                    # Far-right rock
    (250, 130, 180, 65),                    # Upper-left rock
    (500, 0, 350, 80),                      # Top barrier (gap left: 150-500, gap right: 850-1100)
]

# Level 2 rock obstacles (only the non-wall cubes)
level2_rock_cubes = [c for c in level2_cubes if c[2] != 150 or c[3] != HEIGHT]

# Pre-render Level 2 forest (walls only) and rocks (obstacles only)
print("Pre-rendering Level 2...")
level2_wall_cubes = [(0, 0, 150, HEIGHT), (WIDTH - 150, 0, 150, HEIGHT)]
l2_forest = create_forest_surface(
    level2_wall_cubes, WIDTH, HEIGHT, forest_floor, tree_canopy1, tree_canopy2
)
l2_rock_surface = create_rock_surface(level2_rock_cubes, WIDTH, HEIGHT)
print("Level 2 ready.")

l2_foam_points = precompute_foam(level2_cubes, WIDTH, HEIGHT)

# Level 2 state
l2_boat_pos = LEVEL2_INITIAL_POS.copy()
l2_boat_vel = pygame.Vector2(0, 0)
l2_boat_angle = 0
l2_timer = 45
l2_rotating = False
l2_rotation_start_angle = 0
l2_rotation_direction = 0
l2_target_angle = 0
l2_input_buffer = 0
l2_left_pressed = False
l2_right_pressed = False
l2_down_pressed = False

# Level 2 systems
l2_oar = OarAnimator()
l2_wake = WakeSystem()
l2_particles = ParticleSystem()
l2_shake = ScreenShake()
l2_wind = WindSystem()
l2_crash = CrashAnimation()
l2_frame = pygame.Surface((WIDTH, HEIGHT))

# Win screen
l2_win_blink_timer = 0


def reset_level2():
    global l2_boat_pos, l2_boat_vel, l2_boat_angle, l2_timer
    global l2_rotating, l2_rotation_start_angle, l2_rotation_direction, l2_target_angle
    global l2_input_buffer, l2_left_pressed, l2_right_pressed, l2_down_pressed
    global l2_oar, l2_wake, l2_particles, l2_shake, l2_wind, l2_crash
    l2_boat_pos = LEVEL2_INITIAL_POS.copy()
    l2_boat_vel = pygame.Vector2(0, 0)
    l2_boat_angle = 0
    l2_timer = 45
    l2_rotating = False
    l2_rotation_start_angle = 0
    l2_rotation_direction = 0
    l2_target_angle = 0
    l2_input_buffer = 0
    l2_left_pressed = False
    l2_right_pressed = False
    l2_down_pressed = False
    l2_oar = OarAnimator()
    l2_wake = WakeSystem()
    l2_particles = ParticleSystem()
    l2_shake = ScreenShake()
    l2_wind = WindSystem()
    l2_crash = CrashAnimation()


# ================================================================
# MAIN GAME LOOP
# ================================================================
running = True
last_input_time = pygame.time.get_ticks() / 1000.0
input_this_frame = False
game_time = 0


def reset_game():
    """Reset all game state for a fresh start (Level 1)."""
    global boat_pos, boat_velocity, boat_angle, rotating, input_buffer
    global rotation_direction, target_angle, rotation_start_angle
    global left_pressed, right_pressed, down_pressed, timer_seconds
    global l1_crash, l1_shake
    timer_seconds = 60
    boat_pos = INITIAL_BOAT_POS.copy()
    boat_velocity = pygame.Vector2(0, 0)
    boat_angle = 0
    rotating = False
    rotation_direction = 0
    target_angle = 0
    rotation_start_angle = 0
    input_buffer = 0
    left_pressed = False
    right_pressed = False
    down_pressed = False
    wake.clear()
    l1_crash = CrashAnimation()
    l1_shake = ScreenShake()


while running:
    dt = clock.tick(60) / 1000.0
    dt = min(dt, 0.05)  # Cap dt to prevent physics explosion
    current_time = pygame.time.get_ticks() / 1000.0
    game_time += dt

    # Update fade transition globally
    fade.update(dt)

    # ============================================================
    # MENU STATE
    # ============================================================
    if game_state == "menu":
        mouse_pos = pygame.mouse.get_pos()
        mouse_click = False

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mouse_click = True
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                    if not fade.active:
                        def start_game_from_key():
                            global game_state
                            game_state = "playing"
                            reset_game()
                        fade.start(start_game_from_key)

        for btn in menu_buttons:
            if btn.update(mouse_pos, mouse_click, dt):
                if btn is btn_play:
                    if not fade.active:
                        def start_game_from_play():
                            global game_state
                            game_state = "playing"
                            reset_game()
                        fade.start(start_game_from_play)
                elif btn is btn_quit:
                    running = False

        menu_boat_angle = math.sin(game_time * 0.3) * 12
        draw_menu(screen, water, game_time, dt, menu_buttons, menu_boat_angle)
        fade.draw(screen)
        pygame.display.flip()
        continue

    # ============================================================
    # LEVEL 1 COMPLETE STATE
    # ============================================================
    if game_state == "level1_complete":
        l1_complete_timer += dt
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
        water.draw(screen, dt, game_time)
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        screen.blit(overlay, (0, 0))
        complete_text = title_font.render("LEVEL COMPLETE!", True, (50, 255, 80))
        # glow
        glow = title_font.render("LEVEL COMPLETE!", True, (30, 180, 50))
        glow.set_alpha(60)
        screen.blit(glow, glow.get_rect(center=(WIDTH // 2 + 3, HEIGHT // 2 - 57)))
        screen.blit(complete_text, complete_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 60)))
        # Subtitle
        sub = subtitle_font.render("Preparing Level 2...", True, (180, 200, 220))
        screen.blit(sub, sub.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 20)))
        if l1_complete_timer >= 2.0 and not fade.active:
            def start_l2():
                global game_state
                game_state = "level2"
                reset_level2()
            fade.start(start_l2)
        fade.draw(screen)
        pygame.display.flip()
        continue

    # ============================================================
    # LEVEL 2 WIN STATE
    # ============================================================
    if game_state == "level2_win":
        l2_win_blink_timer += dt

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN or event.key == pygame.K_ESCAPE:
                    if not fade.active:
                        def go_menu_from_win():
                            global game_state
                            game_state = "menu"
                        fade.start(go_menu_from_win)

        # Draw water background
        water.draw(screen, dt, game_time)

        # Dark overlay
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        screen.blit(overlay, (0, 0))

        # "YOU WIN!" in green
        complete_text = title_font.render("YOU WIN!", True, (50, 255, 80))
        complete_rect = complete_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 60))
        # Glow
        glow = title_font.render("YOU WIN!", True, (30, 180, 50))
        glow.set_alpha(60)
        screen.blit(glow, glow.get_rect(center=(WIDTH // 2 + 3, HEIGHT // 2 - 57)))
        screen.blit(complete_text, complete_rect)

        # Score
        score_str = f"Time remaining: {l2_timer:.1f}s"
        score_surf = font.render(score_str, True, (255, 255, 200))
        score_rect = score_surf.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 30))
        screen.blit(score_surf, score_rect)

        # Blinking hint
        if int(l2_win_blink_timer * 2) % 2 == 0:
            hint_surf = subtitle_font.render("Press ENTER or ESC", True, (180, 200, 220))
            hint_rect = hint_surf.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 100))
            screen.blit(hint_surf, hint_rect)

        fade.draw(screen)
        pygame.display.flip()
        continue

    # ============================================================
    # LEVEL 2 PLAYING STATE (single-screen, rocks, wind)
    # ============================================================
    if game_state == "level2":
        l2_input_this_frame = False

        # Timer countdown
        l2_timer -= dt
        if l2_timer <= 0:
            l2_timer = 0
            # Time's up - reset
            reset_level2()

        # Update crash animation
        l2_crash.update(dt)
        l2_shake.update(dt)

        # ---- INPUT HANDLING ----
        if l2_crash.active:
            # During crash, only process QUIT/ESC
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        if not fade.active:
                            def go_menu_from_l2_crash():
                                global game_state
                                game_state = "menu"
                            fade.start(go_menu_from_l2_crash)
        else:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        if not fade.active:
                            def go_menu_from_l2():
                                global game_state
                                game_state = "menu"
                            fade.start(go_menu_from_l2)
                        continue
                    if event.key == pygame.K_LEFT:
                        if not l2_left_pressed:
                            l2_left_pressed = True
                            l2_oar.trigger_left()
                            play_paddle_sound()
                            if not l2_rotating:
                                l2_rotation_start_angle = l2_boat_angle
                                l2_rotation_direction = 1
                                l2_target_angle = (l2_rotation_start_angle + ROTATION_STEP) % 360
                                l2_rotating = True
                            else:
                                if l2_rotation_direction == -1:
                                    l2_target_angle = l2_rotation_start_angle % 360
                                    l2_rotation_direction = 0
                        l2_input_buffer += 1
                        last_input_time = current_time
                        l2_input_this_frame = True

                    if event.key == pygame.K_RIGHT:
                        if not l2_right_pressed:
                            l2_right_pressed = True
                            l2_oar.trigger_right()
                            play_paddle_sound()
                            if not l2_rotating:
                                l2_rotation_start_angle = l2_boat_angle
                                l2_rotation_direction = -1
                                l2_target_angle = (l2_rotation_start_angle - ROTATION_STEP) % 360
                                l2_rotating = True
                            else:
                                if l2_rotation_direction == 1:
                                    l2_target_angle = l2_rotation_start_angle % 360
                                    l2_rotation_direction = 0
                        l2_input_buffer += 1
                        last_input_time = current_time
                        l2_input_this_frame = True

                    if event.key == pygame.K_DOWN:
                        if not l2_down_pressed:
                            l2_down_pressed = True
                            l2_oar.trigger_left()
                            l2_oar.trigger_right()
                            play_paddle_sound()
                            if not l2_rotating:
                                l2_rotation_start_angle = l2_boat_angle
                                l2_rotation_direction = 1
                                l2_target_angle = (l2_rotation_start_angle + ROTATION_STEP) % 360
                                l2_rotating = True
                            else:
                                if l2_rotation_direction == -1:
                                    l2_target_angle = l2_rotation_start_angle % 360
                                    l2_rotation_direction = 0
                        last_input_time = current_time
                        l2_input_this_frame = True

                if event.type == pygame.KEYUP:
                    if event.key == pygame.K_LEFT:
                        l2_left_pressed = False
                    if event.key == pygame.K_RIGHT:
                        l2_right_pressed = False
                    if event.key == pygame.K_DOWN:
                        l2_down_pressed = False

            if not l2_input_this_frame:
                if current_time - last_input_time > input_decay_time:
                    l2_input_buffer = 0
                else:
                    l2_input_buffer *= math.exp(-dt / input_decay_time)

            # ---- SMOOTH ROTATION ----
            if l2_rotating:
                diff = (l2_target_angle - l2_boat_angle + 180) % 360 - 180
                max_step = ROTATION_SPEED * dt
                step = math.copysign(min(abs(diff), max_step), diff)
                l2_boat_angle += step
                remaining = (l2_target_angle - l2_boat_angle + 180) % 360 - 180
                if abs(remaining) < 0.01:
                    l2_boat_angle = l2_target_angle % 360
                    l2_rotating = False
                    l2_rotation_direction = 0
            l2_boat_angle %= 360

            # ---- PHYSICS ----
            forward_dir = pygame.Vector2(0, -1).rotate(l2_boat_angle)

            if l2_input_buffer > 0.01:
                total_accel = BASE_ACCEL + ACCEL_PER_PRESS * l2_input_buffer
                if l2_left_pressed != l2_right_pressed:
                    total_accel *= SINGLE_KEY_ACCEL_MULT
                l2_boat_vel += forward_dir * total_accel * dt

            # Apply wind
            l2_wind.update(dt)
            # Wind sound
            if l2_wind.active and l2_wind.gust_timer < dt * 2:
                play_sound(wind_sfx, 0.5)
            wind_force = l2_wind.get_force()
            l2_boat_vel += wind_force * dt

            l2_speed = l2_boat_vel.length()
            if l2_speed > MAX_SPEED:
                l2_boat_vel = (l2_boat_vel / l2_speed) * MAX_SPEED

            if l2_speed > 0.01:
                vel_dir = l2_boat_vel.normalize()
                alignment = vel_dir.dot(forward_dir)
                sideways_factor = abs(alignment)
                sideways_effect = SIDEWAYS_DRIFT_MULT
                if l2_left_pressed != l2_right_pressed:
                    sideways_effect *= SINGLE_KEY_SIDEWAYS_MULT
                friction_mult = (
                    BASE_FRICTION
                    + (1 - sideways_factor)
                    * (SIDEWAYS_FRICTION - BASE_FRICTION)
                    * sideways_effect
                )
                l2_boat_vel *= friction_mult
            else:
                l2_boat_vel = pygame.Vector2(0, 0)

            l2_boat_pos += l2_boat_vel

            # ---- COLLISION DETECTION (crash animation) ----
            for cx, cy, cw, ch in level2_cubes:
                if (
                    l2_boat_pos.x - boat_collision_radius < cx + cw
                    and l2_boat_pos.x + boat_collision_radius > cx
                    and l2_boat_pos.y - boat_collision_radius < cy + ch
                    and l2_boat_pos.y + boat_collision_radius > cy
                ):
                    if not l2_crash.active:
                        l2_shake.trigger(6, 0.5)
                        play_sound(crash_sfx)
                        def l2_respawn():
                            global l2_boat_pos, l2_boat_vel, l2_boat_angle, l2_rotating
                            l2_boat_pos = LEVEL2_INITIAL_POS.copy()
                            l2_boat_vel = pygame.Vector2(0, 0)
                            l2_boat_angle = 0
                            l2_rotating = False
                            l2_wake.clear()
                        l2_crash.trigger(l2_boat_pos, l2_boat_angle, l2_respawn)
                        l2_boat_vel = pygame.Vector2(0, 0)
                    break

            # Clamp boat to screen bounds
            l2_boat_pos.x = max(boat_collision_radius, min(WIDTH - boat_collision_radius, l2_boat_pos.x))
            l2_boat_pos.y = max(0, min(HEIGHT, l2_boat_pos.y))

            # ---- WIN CONDITION ----
            if l2_boat_pos.y < LEVEL2_FINISH_Y and not l2_crash.active:
                if not fade.active:
                    def go_l2_win():
                        global game_state, l2_win_blink_timer
                        game_state = "level2_win"
                        l2_win_blink_timer = 0
                    fade.start(go_l2_win)

        # ---- UPDATE SYSTEMS ----
        l2_oar.update(dt)
        l2_speed_for_draw = l2_boat_vel.length()
        l2_wake.update(dt, l2_boat_pos, l2_boat_angle, l2_speed_for_draw)
        l2_particles.update(dt)

        # ---- DRAWING (to frame buffer for shake offset) ----
        frame = l2_frame

        # 1. Water
        water.draw(frame, dt, game_time)

        # 2. Finish line glow at y=40
        finish_glow_y = LEVEL2_FINISH_Y
        glow_surf = pygame.Surface((WIDTH, 12), pygame.SRCALPHA)
        glow_pulse = 0.5 + 0.5 * math.sin(game_time * 3)
        glow_alpha = int(60 + 80 * glow_pulse)
        glow_surf.fill((80, 255, 120, glow_alpha))
        frame.blit(glow_surf, (0, finish_glow_y - 6))
        pygame.draw.line(frame, (80, 255, 120), (150, finish_glow_y), (WIDTH - 150, finish_glow_y), 2)

        # 3. Shoreline foam
        draw_foam(frame, l2_foam_points, game_time)

        # 4. Forest walls
        frame.blit(l2_forest, (0, 0))

        # 5. Rock obstacles
        frame.blit(l2_rock_surface, (0, 0))

        # 6. Wake
        l2_wake.draw(frame)

        # 7. Crash animation
        l2_crash.draw(frame)

        # 8. Boat (hide during crash)
        if not l2_crash.active:
            draw_boat(frame, l2_boat_pos, l2_boat_angle, l2_oar, l2_speed_for_draw)

        # 9. HUD
        # Timer
        timer_color = (255, 0, 0) if l2_timer <= 10 else (255, 255, 255)
        timer_text = font.render(f"{l2_timer:.1f}", True, timer_color)
        timer_shadow = font.render(f"{l2_timer:.1f}", True, (0, 0, 0))
        timer_rect = timer_text.get_rect(midtop=(WIDTH // 2, 20))
        shadow_rect_t = timer_rect.copy()
        shadow_rect_t.x += 2
        shadow_rect_t.y += 2
        if l2_timer <= 10:
            sx = random.randint(-2, 2)
            sy = random.randint(-2, 2)
            timer_rect.x += sx
            timer_rect.y += sy
            shadow_rect_t.x += sx
            shadow_rect_t.y += sy
        frame.blit(timer_shadow, shadow_rect_t)
        frame.blit(timer_text, timer_rect)

        # Wind indicator (top right)
        if l2_wind.active:
            wind_label = hud_font.render("WIND", True, (255, 255, 200))
            frame.blit(wind_label, (WIDTH - 120, 20))
            # Arrow
            arrow_x = WIDTH - 70
            arrow_y = 55
            wind_f = l2_wind.get_force()
            arrow_len = min(30, int(abs(wind_f.x) * 18))
            arrow_dir = 1 if wind_f.x > 0 else -1
            pygame.draw.line(frame, (255, 255, 100),
                             (arrow_x - arrow_dir * arrow_len, arrow_y),
                             (arrow_x + arrow_dir * arrow_len, arrow_y), 3)
            # Arrowhead
            pygame.draw.polygon(frame, (255, 255, 100), [
                (arrow_x + arrow_dir * arrow_len, arrow_y),
                (arrow_x + arrow_dir * (arrow_len - 8), arrow_y - 5),
                (arrow_x + arrow_dir * (arrow_len - 8), arrow_y + 5),
            ])

        # "Level 2" label (bottom right)
        lvl_label = hud_font.render("Level 2", True, (180, 200, 220))
        frame.blit(lvl_label, (WIDTH - 100, HEIGHT - 35))

        # Blit frame to screen with shake offset
        shake_ox = int(l2_shake.offset_x)
        shake_oy = int(l2_shake.offset_y)
        screen.fill((0, 0, 0))
        screen.blit(frame, (shake_ox, shake_oy))

        fade.draw(screen)
        pygame.display.flip()
        continue

    # ============================================================
    # LEVEL 1 PLAYING STATE
    # ============================================================
    input_this_frame = False

    # Timer countdown
    timer_seconds -= dt
    if timer_seconds <= 0:
        timer_seconds = 60
        boat_pos = INITIAL_BOAT_POS.copy()
        boat_velocity = pygame.Vector2(0, 0)
        boat_angle = 0
        rotating = False
        input_buffer = 0

    # Update crash and shake
    l1_crash.update(dt)
    l1_shake.update(dt)

    # ---- INPUT HANDLING ----
    if l1_crash.active:
        # During crash, only process QUIT/ESC
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if not fade.active:
                        def go_menu_from_l1_crash():
                            global game_state
                            game_state = "menu"
                        fade.start(go_menu_from_l1_crash)
    else:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if not fade.active:
                        def go_menu_from_l1():
                            global game_state
                            game_state = "menu"
                        fade.start(go_menu_from_l1)
                    continue
                if event.key == pygame.K_LEFT:
                    if not left_pressed:
                        left_pressed = True
                        oar_anim.trigger_left()
                        play_paddle_sound()
                        if not rotating:
                            rotation_start_angle = boat_angle
                            rotation_direction = 1
                            target_angle = (rotation_start_angle + ROTATION_STEP) % 360
                            rotating = True
                        else:
                            if rotation_direction == -1:
                                target_angle = rotation_start_angle % 360
                                rotation_direction = 0
                    input_buffer += 1
                    last_input_time = current_time
                    input_this_frame = True

                if event.key == pygame.K_RIGHT:
                    if not right_pressed:
                        right_pressed = True
                        oar_anim.trigger_right()
                        play_paddle_sound()
                        if not rotating:
                            rotation_start_angle = boat_angle
                            rotation_direction = -1
                            target_angle = (rotation_start_angle - ROTATION_STEP) % 360
                            rotating = True
                        else:
                            if rotation_direction == 1:
                                target_angle = rotation_start_angle % 360
                                rotation_direction = 0
                    input_buffer += 1
                    last_input_time = current_time
                    input_this_frame = True

                if event.key == pygame.K_DOWN:
                    if not down_pressed:
                        down_pressed = True
                        oar_anim.trigger_left()
                        oar_anim.trigger_right()
                        play_paddle_sound()
                        if not rotating:
                            rotation_start_angle = boat_angle
                            rotation_direction = 1
                            target_angle = (rotation_start_angle + ROTATION_STEP) % 360
                            rotating = True
                        else:
                            if rotation_direction == -1:
                                target_angle = rotation_start_angle % 360
                                rotation_direction = 0
                    last_input_time = current_time
                    input_this_frame = True

            if event.type == pygame.KEYUP:
                if event.key == pygame.K_LEFT:
                    left_pressed = False
                if event.key == pygame.K_RIGHT:
                    right_pressed = False
                if event.key == pygame.K_DOWN:
                    down_pressed = False

        if not input_this_frame:
            if current_time - last_input_time > input_decay_time:
                input_buffer = 0
            else:
                input_buffer *= math.exp(-dt / input_decay_time)

        # ---- SMOOTH ROTATION ----
        if rotating:
            diff = (target_angle - boat_angle + 180) % 360 - 180
            max_step = ROTATION_SPEED * dt
            step = math.copysign(min(abs(diff), max_step), diff)
            boat_angle += step
            remaining = (target_angle - boat_angle + 180) % 360 - 180
            if abs(remaining) < 0.01:
                boat_angle = target_angle % 360
                rotating = False
                rotation_direction = 0
        boat_angle %= 360

        # ---- PHYSICS ----
        forward_direction = pygame.Vector2(0, -1).rotate(boat_angle)

        if input_buffer > 0.01:
            total_accel = BASE_ACCEL + ACCEL_PER_PRESS * input_buffer
            if left_pressed != right_pressed:
                total_accel *= SINGLE_KEY_ACCEL_MULT
            boat_velocity += forward_direction * total_accel * dt

        speed = boat_velocity.length()
        if speed > MAX_SPEED:
            boat_velocity = (boat_velocity / speed) * MAX_SPEED

        if speed > 0.01:
            velocity_direction = boat_velocity.normalize()
            alignment = velocity_direction.dot(forward_direction)
            sideways_factor = abs(alignment)
            sideways_effect_multiplier = SIDEWAYS_DRIFT_MULT
            if left_pressed != right_pressed:
                sideways_effect_multiplier *= SINGLE_KEY_SIDEWAYS_MULT
            friction_multiplier = (
                BASE_FRICTION
                + (1 - sideways_factor)
                * (SIDEWAYS_FRICTION - BASE_FRICTION)
                * sideways_effect_multiplier
            )
            boat_velocity *= friction_multiplier
        else:
            boat_velocity = pygame.Vector2(0, 0)

        boat_pos += boat_velocity

        # ---- COLLISION DETECTION ----
        for cube_x, cube_y, cube_w, cube_h in cubes:
            if (
                boat_pos.x - boat_collision_radius < cube_x + cube_w
                and boat_pos.x + boat_collision_radius > cube_x
                and boat_pos.y - boat_collision_radius < cube_y + cube_h
                and boat_pos.y + boat_collision_radius > cube_y
            ):
                if not l1_crash.active:
                    l1_shake.trigger(6, 0.5)
                    play_sound(crash_sfx)
                    def l1_respawn():
                        global boat_pos, boat_velocity, boat_angle, rotating
                        boat_pos = INITIAL_BOAT_POS.copy()
                        boat_velocity = pygame.Vector2(0, 0)
                        boat_angle = 0
                        rotating = False
                        wake.clear()
                    l1_crash.trigger(boat_pos, boat_angle, l1_respawn)
                    boat_velocity = pygame.Vector2(0, 0)
                break

        # ---- WIN CONDITION ----
        if boat_pos.y < 40 and not l1_crash.active:
            if not fade.active:
                def go_level1_complete():
                    global game_state, l1_complete_timer
                    game_state = "level1_complete"
                    l1_complete_timer = 0
                fade.start(go_level1_complete)

    # ---- UPDATE ANIMATIONS ----
    oar_anim.update(dt)
    wake.update(dt, boat_pos, boat_angle, boat_velocity.length())

    # ---- DRAWING (to frame buffer for shake) ----
    frame = l1_frame

    # 1. Animated water background
    water.draw(frame, dt, game_time)

    # 2. Exit glow indicator at finish gap (top of screen, between obstacles)
    # The gap is between left wall (0-200) and obstacle at (330,0,720,230),
    # so passable area is x=200 to x=330
    glow_pulse = 0.5 + 0.5 * math.sin(game_time * 3)
    glow_alpha = int(60 + 80 * glow_pulse)
    # Draw glow line at y=0 area in the gap
    glow_surf = pygame.Surface((130, 12), pygame.SRCALPHA)
    glow_surf.fill((80, 255, 120, glow_alpha))
    frame.blit(glow_surf, (200, 0))
    pygame.draw.line(frame, (80, 255, 120), (200, 6), (330, 6), 2)

    # 3. Shoreline foam (before forest so it's partly hidden at edges)
    draw_foam(frame, foam_points, game_time)

    # 4. Pre-rendered forest overlay
    frame.blit(forest_surface, (0, 0))

    # 5. Wake trail
    wake.draw(frame)

    # 6. Crash animation
    l1_crash.draw(frame)

    # 7. Boat with animated oars (hide during crash)
    if not l1_crash.active:
        draw_boat(frame, boat_pos, boat_angle, oar_anim, boat_velocity.length())

    # 8. Timer display with drop shadow
    timer_color = (255, 0, 0) if timer_seconds <= 10 else (255, 255, 255)
    timer_text = font.render(f"{timer_seconds:.1f}", True, timer_color)
    timer_shadow = font.render(f"{timer_seconds:.1f}", True, (0, 0, 0))
    timer_rect = timer_text.get_rect(midtop=(WIDTH // 2, 20))
    shadow_rect = timer_rect.copy()
    shadow_rect.x += 2
    shadow_rect.y += 2

    if timer_seconds <= 10:
        sx = random.randint(-2, 2)
        sy = random.randint(-2, 2)
        timer_rect.x += sx
        timer_rect.y += sy
        shadow_rect.x += sx
        shadow_rect.y += sy

    frame.blit(timer_shadow, shadow_rect)
    frame.blit(timer_text, timer_rect)

    # Blit frame to screen with shake offset
    shake_ox = int(l1_shake.offset_x)
    shake_oy = int(l1_shake.offset_y)
    screen.fill((0, 0, 0))
    screen.blit(frame, (shake_ox, shake_oy))

    fade.draw(screen)
    pygame.display.flip()

pygame.quit()
sys.exit()
