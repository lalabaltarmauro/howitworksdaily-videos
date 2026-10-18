"""
stickman.py — personaje de palitos mejorado para How It Works Daily.

Dibuja con cairo (antialiasing real, trazos redondeados) un monigote articulado:
- Esqueleto con hombros, codos, caderas y rodillas (brazos y piernas "de goma").
- Cara expresiva: ojos con brillo y parpadeo, cejas, varias bocas y sincronía labial.
- Camiseta de color de marca, manos y pies redondos, sombra en el suelo.
- Squash & stretch, salto, inclinación y temblor de línea "dibujado a mano".
- Accesorios: gafas de disfraz, bigote, gota de sudor, signos de interrogación.

Uso mínimo:
    import cairo
    from stickman import Character, POSES, draw_character
    ch = Character(x=540, ground=1500, scale=1.0)
    ch.pose = POSES["wave"]
    draw_character(ctx, ch, t=0.0, frame=0)
"""
import math
import random
from dataclasses import dataclass, field

# ---------------------------------------------------------------- paleta
INK = (0.11, 0.11, 0.17)          # contorno
SKIN = (1.0, 1.0, 1.0)            # cabeza
ACCENT = (0.98, 0.42, 0.20)       # naranja marca (camiseta)
BLUSH = (1.0, 0.45, 0.45)
SWEAT = (0.35, 0.70, 1.0)

# ---------------------------------------------------------------- medidas
HEAD_R = 72
NECK = 14
TORSO = 165
UPPER_ARM = 88
LOWER_ARM = 82
THIGH = 98
SHIN = 96
LINE = 14


def lerp(a, b, t):
    return a + (b - a) * t


def ease_in_out(t):
    t = max(0.0, min(1.0, t))
    return 4 * t * t * t if t < 0.5 else 1 - (-2 * t + 2) ** 3 / 2


def ease_out_back(t, s=1.70158):
    t = max(0.0, min(1.0, t))
    t -= 1
    return t * t * ((s + 1) * t + s) + 1


def ease_out_elastic(t):
    t = max(0.0, min(1.0, t))
    if t in (0, 1):
        return t
    return 2 ** (-10 * t) * math.sin((t * 10 - 0.75) * (2 * math.pi) / 3) + 1


def vec(angle_deg, length):
    """0° = hacia abajo, 90° = derecha de pantalla, 180° = arriba, -90° = izquierda."""
    a = math.radians(angle_deg)
    return math.sin(a) * length, math.cos(a) * length


# ---------------------------------------------------------------- poses
# Ángulos absolutos para el segmento superior y relativos para el inferior.
# la = brazo izquierdo de pantalla, ra = derecho, ll/rl = piernas.
POSE_KEYS = ["lean", "head", "la_u", "la_l", "ra_u", "ra_l",
             "ll_u", "ll_l", "rl_u", "rl_l"]

POSES = {
    "idle":      dict(lean=0, head=0, la_u=-14, la_l=-6, ra_u=14, ra_l=6,
                      ll_u=-7, ll_l=2, rl_u=7, rl_l=-2),
    "wave":      dict(lean=-3, head=-6, la_u=-14, la_l=-6, ra_u=122, ra_l=32,
                      ll_u=-7, ll_l=2, rl_u=7, rl_l=-2),
    "point":     dict(lean=4, head=6, la_u=-14, la_l=-6, ra_u=96, ra_l=-4,
                      ll_u=-9, ll_l=2, rl_u=9, rl_l=-2),
    "hips":      dict(lean=0, head=-4, la_u=-48, la_l=95, ra_u=48, ra_l=-95,
                      ll_u=-10, ll_l=2, rl_u=10, rl_l=-2),
    "shrug":     dict(lean=0, head=8, la_u=-55, la_l=-85, ra_u=55, ra_l=85,
                      ll_u=-7, ll_l=2, rl_u=7, rl_l=-2),
    "think":     dict(lean=-2, head=-8, la_u=-10, la_l=-4, ra_u=128, ra_l=145,
                      ll_u=-7, ll_l=2, rl_u=7, rl_l=-2),
    "glasses":   dict(lean=0, head=0, la_u=-48, la_l=95, ra_u=140, ra_l=87,
                      ll_u=-10, ll_l=2, rl_u=10, rl_l=-2),
    "crouch":    dict(lean=6, head=4, la_u=-35, la_l=-25, ra_u=35, ra_l=25,
                      ll_u=-48, ll_l=82, rl_u=48, rl_l=-82),
    "jump":      dict(lean=0, head=0, la_u=-130, la_l=-30, ra_u=130, ra_l=30,
                      ll_u=-18, ll_l=30, rl_u=18, rl_l=-30),
    "surprised": dict(lean=-4, head=-5, la_u=-122, la_l=-38, ra_u=122, ra_l=38,
                      ll_u=-12, ll_l=2, rl_u=12, rl_l=-2),
}


def mix_pose(a, b, t):
    return {k: lerp(a[k], b[k], t) for k in POSE_KEYS}


class Timeline:
    """Lista de (tiempo, pose) que se interpola con suavizado."""

    def __init__(self, keys):
        self.keys = sorted(keys, key=lambda k: k[0])

    def at(self, t):
        ks = self.keys
        if t <= ks[0][0]:
            return dict(ks[0][1])
        for (t0, p0), (t1, p1) in zip(ks, ks[1:]):
            if t0 <= t <= t1:
                return mix_pose(p0, p1, ease_in_out((t - t0) / max(1e-6, t1 - t0)))
        return dict(ks[-1][1])


# ---------------------------------------------------------------- cara
@dataclass
class Face:
    mouth: str = "smile"      # smile, grin, talk, o, frown, flat, smug
    mouth_open: float = 0.0   # 0-1 para "talk"
    brow_raise: float = 0.0   # -1 enfadado .. 1 sorprendido
    brow_tilt: float = 0.0    # + preocupado (cejas en "/\")
    look: tuple = (0.0, 0.0)  # -1..1 dirección de la mirada
    eye_open: float = 1.0     # lo controla el parpadeo
    eye_scale: float = 1.0    # ojos grandes en sorpresa
    blush: float = 0.35


@dataclass
class Character:
    x: float = 540
    ground: float = 1500
    scale: float = 1.0
    facing: int = 1                    # 1 o -1 (espejo)
    pose: dict = field(default_factory=lambda: dict(POSES["idle"]))
    face: Face = field(default_factory=Face)
    accent: tuple = ACCENT
    lift: float = 0.0                  # altura de salto en px
    squash: float = 0.0                # + aplastado, - estirado
    props: dict = field(default_factory=dict)   # glasses, mustache, sweat, question
    seed: int = 7
    boil: float = 1.3                  # amplitud del temblor a mano (px)
    breathe: bool = True


# ---------------------------------------------------------------- utilidades de dibujo
def _jit(ch, frame, key):
    if ch.boil <= 0:
        return 0.0, 0.0
    r = random.Random(hash((ch.seed, frame // 3, key)))   # cambia cada 3 frames
    return r.uniform(-ch.boil, ch.boil), r.uniform(-ch.boil, ch.boil)


def _limb(ctx, a, elbow, b, width, color=INK):
    """Brazo/pierna de goma: curva que pasa por el codo."""
    cx = (elbow[0] - 0.125 * a[0] - 0.125 * b[0]) / 0.75
    cy = (elbow[1] - 0.125 * a[1] - 0.125 * b[1]) / 0.75
    ctx.move_to(*a)
    ctx.curve_to(cx, cy, cx, cy, *b)
    ctx.set_source_rgb(*color)
    ctx.set_line_width(width)
    ctx.set_line_cap(1)   # ROUND
    ctx.set_line_join(1)
    ctx.stroke()


def _circle(ctx, x, y, r, fill, stroke=INK, lw=LINE * 0.7):
    ctx.arc(x, y, r, 0, 2 * math.pi)
    ctx.set_source_rgb(*fill)
    ctx.fill_preserve()
    ctx.set_source_rgb(*stroke)
    ctx.set_line_width(lw)
    ctx.stroke()


def solve_skeleton(ch, t=0.0):
    """Devuelve puntos del esqueleto en coordenadas locales (pies en y=0)."""
    p = ch.pose
    breath = math.sin(t * 2 * math.pi * 0.45) * 2.5 if ch.breathe else 0
    hip = (0.0, 0.0)
    legs = {}
    for side, sx in (("l", -14), ("r", 14)):
        h = (hip[0] + sx, hip[1])
        k = (h[0] + vec(p[f"{side}l_u"], THIGH)[0], h[1] + vec(p[f"{side}l_u"], THIGH)[1])
        a = p[f"{side}l_u"] + p[f"{side}l_l"]
        f = (k[0] + vec(a, SHIN)[0], k[1] + vec(a, SHIN)[1])
        legs[side] = (h, k, f)
    lowest = max(legs["l"][2][1], legs["r"][2][1])
    shift = -lowest          # sube todo para que el pie más bajo toque el suelo
    tor_a = 180 + p["lean"]
    neck = (hip[0] + vec(tor_a, TORSO + breath)[0], hip[1] + vec(tor_a, TORSO + breath)[1])
    shoulder = (neck[0] + vec(tor_a, -26)[0], neck[1] + vec(tor_a, -26)[1])
    arms = {}
    for side, sx in (("l", -1), ("r", 1)):
        perp = vec(tor_a - 90, 1)
        s = (shoulder[0] + perp[0] * 27 * sx, shoulder[1] + perp[1] * 27 * sx)
        u = p[f"{side}a_u"]
        e = (s[0] + vec(u, UPPER_ARM)[0], s[1] + vec(u, UPPER_ARM)[1])
        a = u + p[f"{side}a_l"]
        hnd = (e[0] + vec(a, LOWER_ARM)[0], e[1] + vec(a, LOWER_ARM)[1])
        arms[side] = (s, e, hnd)
    head_a = tor_a + p["head"] * 0.3
    hc = (neck[0] + vec(head_a, NECK + HEAD_R)[0], neck[1] + vec(head_a, NECK + HEAD_R)[1])

    def mv(pt):
        return (pt[0], pt[1] + shift)

    return dict(
        hip=mv(hip), neck=mv(neck), head=mv(hc), head_rot=p["lean"] + p["head"],
        legs={k: tuple(mv(q) for q in v) for k, v in legs.items()},
        arms={k: tuple(mv(q) for q in v) for k, v in arms.items()},
    )


# ---------------------------------------------------------------- partes
def _draw_shirt(ctx, sk, accent):
    hip, neck = sk["hip"], sk["neck"]
    dx, dy = neck[0] - hip[0], neck[1] - hip[1]
    ln = math.hypot(dx, dy)
    ux, uy = dx / ln, dy / ln
    px, py = -uy, ux
    top_w, bot_w = 34, 30
    top = (neck[0] - ux * 6, neck[1] - uy * 6)
    bot = (hip[0] - ux * 10, hip[1] - uy * 10)
    ctx.move_to(top[0] + px * top_w, top[1] + py * top_w)
    ctx.curve_to(top[0] + px * (top_w + 8) - ux * ln * 0.45, top[1] + py * (top_w + 8) - uy * ln * 0.45,
                 bot[0] + px * (bot_w + 6) + ux * 20, bot[1] + py * (bot_w + 6) + uy * 20,
                 bot[0] + px * bot_w, bot[1] + py * bot_w)
    ctx.line_to(bot[0] - px * bot_w, bot[1] - py * bot_w)
    ctx.curve_to(bot[0] - px * (bot_w + 6) + ux * 20, bot[1] - py * (bot_w + 6) + uy * 20,
                 top[0] - px * (top_w + 8) - ux * ln * 0.45, top[1] - py * (top_w + 8) - uy * ln * 0.45,
                 top[0] - px * top_w, top[1] - py * top_w)
    ctx.close_path()
    ctx.set_source_rgb(*accent)
    ctx.fill_preserve()
    ctx.set_source_rgb(*INK)
    ctx.set_line_width(LINE * 0.75)
    ctx.set_line_join(1)
    ctx.stroke()
    # cuello de la camiseta
    ctx.arc(top[0], top[1], 15, 0, 2 * math.pi)
    ctx.set_source_rgb(*SKIN)
    ctx.fill()


def _draw_foot(ctx, knee, foot, facing):
    ctx.save()
    ctx.translate(foot[0] + 10 * facing, foot[1] - 4)
    ctx.scale(1.0, 0.62)
    ctx.arc(0, 0, 22, 0, 2 * math.pi)
    ctx.restore()
    ctx.set_source_rgb(*INK)
    ctx.fill()


def _draw_eye(ctx, x, y, f, frame_scale=1.0):
    rx, ry = 10 * f.eye_scale, 14 * f.eye_scale
    lx, ly = f.look[0] * 5, f.look[1] * 4
    op = max(0.0, min(1.0, f.eye_open))
    if op < 0.15:
        ctx.move_to(x - rx, y + 2)
        ctx.curve_to(x - rx * 0.4, y + 6, x + rx * 0.4, y + 6, x + rx, y + 2)
        ctx.set_source_rgb(*INK)
        ctx.set_line_width(5)
        ctx.stroke()
        return
    ctx.save()
    ctx.translate(x + lx, y + ly)
    ctx.scale(1.0, op)
    ctx.arc(0, 0, rx, 0, 2 * math.pi)
    ctx.restore()
    ctx.set_source_rgb(*INK)
    ctx.fill()
    if op > 0.5:  # brillo
        ctx.arc(x + lx + rx * 0.35, y + ly - ry * 0.35 * op, rx * 0.38, 0, 2 * math.pi)
        ctx.set_source_rgb(1, 1, 1)
        ctx.fill()


def _draw_face(ctx, f, props, t):
    # rubor
    if f.blush > 0:
        for sx in (-1, 1):
            ctx.save()
            ctx.translate(sx * 44, 22)
            ctx.scale(1.4, 0.8)
            ctx.arc(0, 0, 11, 0, 2 * math.pi)
            ctx.restore()
            ctx.set_source_rgba(*BLUSH, f.blush)
            ctx.fill()
    # ojos
    for sx in (-1, 1):
        _draw_eye(ctx, sx * 24, -4, f)
    # cejas
    ctx.set_source_rgb(*INK)
    ctx.set_line_width(6.5)
    ctx.set_line_cap(1)
    by = -30 - f.brow_raise * 9 - (f.eye_scale - 1) * 10
    for sx in (-1, 1):
        inner = (sx * 13, by + f.brow_tilt * -6 + max(0, -f.brow_raise) * 4)
        outer = (sx * 36, by + f.brow_tilt * 6 - max(0, -f.brow_raise) * 4)
        mid = ((inner[0] + outer[0]) / 2, (inner[1] + outer[1]) / 2 - 3)
        ctx.move_to(*inner)
        ctx.curve_to(mid[0], mid[1], mid[0], mid[1], *outer)
        ctx.stroke()
    # boca
    my = 30
    m = f.mouth
    ctx.set_line_width(6.5)
    if m == "smile":
        ctx.move_to(-18, my - 2)
        ctx.curve_to(-8, my + 12, 8, my + 12, 18, my - 2)
        ctx.stroke()
    elif m == "grin":
        ctx.move_to(-22, my - 4)
        ctx.curve_to(-10, my + 22, 10, my + 22, 22, my - 4)
        ctx.close_path()
        ctx.set_source_rgb(*INK)
        ctx.fill_preserve()
        ctx.stroke()
        ctx.arc(0, my + 11, 7, 0, math.pi)
        ctx.set_source_rgb(1, 0.5, 0.55)
        ctx.fill()
    elif m in ("talk", "o"):
        op = f.mouth_open if m == "talk" else 1.0
        w = 16 if m == "talk" else 12
        h = 3 + 15 * op if m == "talk" else 17
        ctx.save()
        ctx.translate(0, my + 2)
        ctx.scale(w, max(h, 2.5))
        ctx.arc(0, 0, 1, 0, 2 * math.pi)
        ctx.restore()
        ctx.set_source_rgb(*INK)
        ctx.fill()
        if h > 8:
            ctx.save()
            ctx.translate(0, my + 2 + h * 0.45)
            ctx.scale(w * 0.6, h * 0.35)
            ctx.arc(0, 0, 1, math.pi, 2 * math.pi)
            ctx.restore()
            ctx.set_source_rgb(1, 0.5, 0.55)
            ctx.fill()
    elif m == "frown":
        ctx.move_to(-16, my + 8)
        ctx.curve_to(-6, my - 4, 6, my - 4, 16, my + 8)
        ctx.stroke()
    elif m == "flat":
        ctx.move_to(-13, my + 3)
        ctx.line_to(13, my + 1)
        ctx.stroke()
    elif m == "smug":
        ctx.move_to(-16, my + 2)
        ctx.curve_to(-4, my + 8, 8, my + 6, 20, my - 6)
        ctx.stroke()
    # accesorios de cara
    if props.get("mustache", 0) > 1e-3:
        s = props["mustache"]
        ctx.save()
        ctx.translate(0, 17)
        ctx.scale(s, s)
        for sx in (-1, 1):
            ctx.move_to(0, -2)
            ctx.curve_to(sx * 10, -12, sx * 30, -10, sx * 36, 4)
            ctx.curve_to(sx * 28, 0, sx * 14, 8, 0, 4)
            ctx.close_path()
        ctx.set_source_rgb(0.25, 0.16, 0.10)
        ctx.fill()
        ctx.restore()
    if props.get("glasses", 0) > 1e-3:
        s = props["glasses"]
        ctx.save()
        ctx.translate(0, -4)
        ctx.scale(s, s)
        for sx in (-1, 1):
            ctx.arc(sx * 25, 0, 20, 0, 2 * math.pi)
            ctx.set_source_rgba(0.1, 0.1, 0.18, 0.88)
            ctx.fill_preserve()
            ctx.set_source_rgb(*INK)
            ctx.set_line_width(6)
            ctx.stroke()
            ctx.move_to(sx * 25 - 8, -9)          # reflejo
            ctx.line_to(sx * 25 + 2, -12)
            ctx.set_source_rgba(1, 1, 1, 0.8)
            ctx.set_line_width(4)
            ctx.stroke()
        ctx.move_to(-6, -2)
        ctx.curve_to(-2, -8, 2, -8, 6, -2)
        ctx.set_source_rgb(*INK)
        ctx.set_line_width(6)
        ctx.stroke()
        for sx in (-1, 1):
            ctx.move_to(sx * 45, -2)
            ctx.line_to(sx * 66, -8)
            ctx.stroke()
        ctx.restore()


def _draw_sweat(ctx, x, y, s):
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(s, s)
    ctx.move_to(0, -22)
    ctx.curve_to(6, -10, 13, 0, 13, 7)
    ctx.curve_to(13, 15, 6, 20, 0, 20)
    ctx.curve_to(-6, 20, -13, 15, -13, 7)
    ctx.curve_to(-13, 0, -6, -10, 0, -22)
    ctx.set_source_rgb(*SWEAT)
    ctx.fill_preserve()
    ctx.set_source_rgb(*INK)
    ctx.set_line_width(4)
    ctx.stroke()
    ctx.restore()


def draw_shadow(ctx, ch):
    w = 95 * ch.scale * max(0.45, 1 - ch.lift / 500)
    a = 0.18 * max(0.3, 1 - ch.lift / 450)
    ctx.save()
    ctx.translate(ch.x, ch.ground + 6 * ch.scale)
    ctx.scale(w, 14 * ch.scale)
    ctx.arc(0, 0, 1, 0, 2 * math.pi)
    ctx.restore()
    ctx.set_source_rgba(0, 0, 0, a)
    ctx.fill()


def draw_character(ctx, ch, t=0.0, frame=0):
    sk = solve_skeleton(ch, t)
    draw_shadow(ctx, ch)
    ctx.save()
    ctx.translate(ch.x, ch.ground - ch.lift)
    sq = ch.squash
    ctx.scale(ch.scale * ch.facing * (1 + sq * 0.5), ch.scale * (1 - sq))

    def J(pt, key):
        j = _jit(ch, frame, key)
        return pt[0] + j[0], pt[1] + j[1]

    # piernas
    for side in ("l", "r"):
        h, k, f = sk["legs"][side]
        _limb(ctx, J(h, side + "h"), J(k, side + "k"), J(f, side + "f"), LINE)
        _draw_foot(ctx, k, J(f, side + "f"), -1 if side == "l" else 1)
    def draw_arm(side):
        s, e, hnd = sk["arms"][side]
        _limb(ctx, J(s, side + "s"), J(e, side + "e"), J(hnd, side + "w"), LINE)
        ax, ay = J(hnd, side + "w")
        _circle(ctx, ax, ay, 13, SKIN, lw=LINE * 0.6)
        # manga corta del color de la camiseta
        sx_, sy_ = J(s, side + "s")
        ex, ey = J(e, side + "e")
        dx, dy = ex - sx_, ey - sy_
        ln = max(1e-6, (dx * dx + dy * dy) ** 0.5)
        ctx.move_to(sx_, sy_)
        ctx.line_to(sx_ + dx / ln * 26, sy_ + dy / ln * 26)
        ctx.set_line_cap(1)
        ctx.set_source_rgb(*INK)
        ctx.set_line_width(LINE + 22)
        ctx.stroke_preserve()
        ctx.set_source_rgb(*ch.accent)
        ctx.set_line_width(LINE + 11)
        ctx.stroke()

    front = []
    hcx, hcy = sk["head"]
    for side in ("l", "r"):
        hnd = sk["arms"][side][2]
        if (hnd[0] - hcx) ** 2 + (hnd[1] - hcy) ** 2 < (HEAD_R + 30) ** 2:
            front.append(side)
        else:
            draw_arm(side)
    _draw_shirt(ctx, sk, ch.accent)
    # cabeza
    hx, hy = J(sk["head"], "head")
    ctx.save()
    ctx.translate(hx, hy)
    ctx.rotate(math.radians(-sk["head_rot"]))
    _circle(ctx, 0, 0, HEAD_R, SKIN, lw=LINE * 0.8)
    # tres pelos para dar personalidad
    ctx.set_source_rgb(*INK)
    ctx.set_line_width(6)
    ctx.set_line_cap(1)
    for i, a in enumerate((-12, 0, 14)):
        x0, y0 = vec(180 + a, HEAD_R - 2)
        x1, y1 = vec(180 + a * 1.6 + 6, HEAD_R + 20 + (i == 1) * 6)
        ctx.move_to(x0, y0)
        ctx.curve_to(x0 + 6, y0 - 12, x1 - 4, y1 + 6, x1, y1)
        ctx.stroke()
    _draw_face(ctx, ch.face, ch.props, t)
    ctx.restore()
    for side in front:
        draw_arm(side)
    # gota de sudor y signo de pregunta
    if ch.props.get("sweat", 0) > 1e-3:
        _draw_sweat(ctx, hx + 78, hy - 46, ch.props["sweat"])
    if ch.props.get("question", 0) > 1e-3:
        q = ch.props["question"]
        ctx.save()
        ctx.translate(hx + 95, hy - 95)
        ctx.scale(q, q)
        ctx.select_font_face("Poppins", 0, 1)
        ctx.set_font_size(78)
        ctx.move_to(-20, 25)
        ctx.text_path("?")
        ctx.set_source_rgb(*ch.accent)
        ctx.fill_preserve()
        ctx.set_source_rgb(*INK)
        ctx.set_line_width(4)
        ctx.stroke()
        ctx.restore()
    ctx.restore()


def blink_amount(t, seed=0, period=3.1):
    """Parpadeo natural: cerrado ~0.12 s cada ~3 s con variación."""
    r = random.Random(seed)
    offset = r.uniform(0, period)
    phase = (t + offset) % period
    if phase < 0.12:
        return abs(phase - 0.06) / 0.06
    return 1.0


def talk_amount(t, speed=11.0):
    """Apertura de boca pseudo-aleatoria para sincronía labial sin audio."""
    v = (math.sin(t * speed) + math.sin(t * speed * 1.7 + 1.3) * 0.6 + 1.6) / 3.2
    return max(0.0, min(1.0, v))
