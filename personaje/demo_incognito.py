"""Demo: gancho del vídeo 'Incognito Isn't Invisible' con el personaje mejorado.

python3 demo_incognito.py salida.mp4 [frame_suelto.png tiempo]
"""
import math
import subprocess
import sys

import cairo

from stickman import (ACCENT, INK, Character, Face, POSES, Timeline, blink_amount,
                      draw_character, ease_out_back, ease_out_elastic, talk_amount)

W, H, FPS, DUR = 1080, 1920, 30, 8.0

timeline = Timeline([
    (0.0, POSES["idle"]), (0.35, POSES["wave"]), (1.6, POSES["wave"]),
    (1.9, POSES["glasses"]), (2.5, POSES["glasses"]),
    (2.8, POSES["hips"]), (4.7, POSES["hips"]),
    (5.0, POSES["crouch"]), (5.2, POSES["crouch"]),
    (5.4, POSES["surprised"]), (6.3, POSES["surprised"]),
    (6.7, POSES["shrug"]), (8.0, POSES["shrug"]),
])

WATCHERS = [(175, 560, "ISP", 3.7), (540, 470, "WI-FI", 4.0), (905, 560, "WEBSITE", 4.3)]


def background(ctx):
    g = cairo.LinearGradient(0, 0, 0, H)
    g.add_color_stop_rgb(0, 0.98, 0.96, 0.92)
    g.add_color_stop_rgb(1, 0.91, 0.88, 0.81)
    ctx.set_source(g)
    ctx.paint()
    # puntos sutiles de cuaderno
    ctx.set_source_rgba(*INK, 0.06)
    for y in range(60, H, 60):
        for x in range(60, W, 60):
            ctx.arc(x, y, 2.2, 0, 2 * math.pi)
            ctx.fill()


def pill_text(ctx, text, cx, cy, size, fg, bg, pad=22, scale=1.0, rot=0.0):
    ctx.save()
    ctx.translate(cx, cy)
    ctx.rotate(rot)
    ctx.scale(scale, scale)
    ctx.select_font_face("Poppins", 0, 1)
    ctx.set_font_size(size)
    e = ctx.text_extents(text)
    w, h = e.width + pad * 2, size * 1.25
    x, y, r = -w / 2, -h / 2, 18
    ctx.new_sub_path()
    ctx.arc(x + w - r, y + r, r, -math.pi / 2, 0)
    ctx.arc(x + w - r, y + h - r, r, 0, math.pi / 2)
    ctx.arc(x + r, y + h - r, r, math.pi / 2, math.pi)
    ctx.arc(x + r, y + r, r, math.pi, 3 * math.pi / 2)
    ctx.close_path()
    ctx.set_source_rgb(*bg)
    ctx.fill_preserve()
    ctx.set_source_rgb(*INK)
    ctx.set_line_width(6)
    ctx.stroke()
    ctx.move_to(-e.width / 2 - e.x_bearing, -e.height / 2 - e.y_bearing)
    ctx.set_source_rgb(*fg)
    ctx.show_text(text)
    ctx.restore()


def caption(ctx, t):
    s1 = ease_out_back(t / 0.35)
    s2 = ease_out_back((t - 0.25) / 0.35)
    if s1 > 1e-3:
        pill_text(ctx, "INCOGNITO", W / 2, 200, 104, INK, (1, 1, 1), scale=s1, rot=-0.03)
    if s2 > 1e-3:
        pill_text(ctx, "ISN'T INVISIBLE", W / 2, 340, 74, (1, 1, 1), ACCENT, scale=s2, rot=0.02)


def watcher(ctx, x, y, label, t_in, t, target):
    s = ease_out_elastic((t - t_in) / 0.7)
    if t <= t_in or abs(s) < 1e-3:
        return
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(s, s)
    w, h = 92, 54
    op = blink_amount(t, seed=hash(label) % 97, period=2.3)

    def almond():
        ctx.move_to(-w, 0)
        ctx.curve_to(-w * 0.5, -h * 1.35 * op, w * 0.5, -h * 1.35 * op, w, 0)
        ctx.curve_to(w * 0.5, h * 1.35 * op, -w * 0.5, h * 1.35 * op, -w, 0)
        ctx.close_path()

    almond()
    ctx.set_source_rgb(1, 1, 1)
    ctx.fill_preserve()
    ctx.save()
    ctx.clip()
    dx, dy = target[0] - x, target[1] - y
    d = max(1, math.hypot(dx, dy))
    px, py = dx / d * 26, dy / d * 18
    ctx.arc(px, py, 40, 0, 2 * math.pi)
    ctx.set_source_rgb(0.30, 0.55, 0.85)
    ctx.fill()
    ctx.arc(px, py, 20, 0, 2 * math.pi)
    ctx.set_source_rgb(*INK)
    ctx.fill()
    ctx.arc(px + 12, py - 12, 9, 0, 2 * math.pi)
    ctx.set_source_rgb(1, 1, 1)
    ctx.fill()
    ctx.restore()
    almond()
    ctx.set_source_rgb(*INK)
    ctx.set_line_width(9)
    ctx.stroke()
    # pestañas
    ctx.set_line_width(7)
    ctx.set_line_cap(1)
    for a in (-0.55, 0, 0.55):
        bx, by = math.sin(a) * w * 0.55, -h * 1.0 * op - 2
        ctx.move_to(bx, by)
        ctx.line_to(bx + math.sin(a) * 20, by - 22)
        ctx.stroke()
    ctx.restore()
    if s > 0.3:
        pill_text(ctx, label, x, y + 95, 40, (1, 1, 1), INK, scale=min(1, s))


SUBS = [(0.4, 1.9, ["You", "open", "incognito…"]),
        (5.6, 8.0, ["Three", "people", "still", "can."])]


def subtitles(ctx, t):
    for t0, t1, words in SUBS:
        if not (t0 <= t < t1):
            continue
        ctx.select_font_face("Poppins", 0, 1)
        ctx.set_font_size(70)
        widths = [ctx.text_extents(w + " ").x_advance for w in words]
        x = W / 2 - sum(widths) / 2
        per = min(0.32, (t1 - t0) / (len(words) + 1))
        for i, (wd, wv) in enumerate(zip(words, widths)):
            ti = t0 + i * per
            if t < ti:
                break
            pop = ease_out_back((t - ti) / 0.18)
            if pop < 1e-3:
                break
            active = ti <= t < ti + per
            ctx.save()
            ctx.translate(x + wv / 2, 1790)
            ctx.scale(pop, pop)
            ctx.move_to(-wv / 2, 0)
            ctx.text_path(wd)
            ctx.set_line_width(14)
            ctx.set_line_join(1)
            ctx.set_source_rgb(*INK)
            ctx.stroke_preserve()
            ctx.set_source_rgb(*(ACCENT if active else (1, 1, 1)))
            ctx.fill()
            ctx.restore()
            x += wv


def render_frame(ctx, frame):
    t = frame / FPS
    # rebote de cámara al aterrizar
    shake = 0
    if 5.75 <= t < 6.05:
        shake = math.sin((t - 5.75) * 60) * 8 * (1 - (t - 5.75) / 0.3)
    ctx.save()
    ctx.translate(0, shake)
    background(ctx)
    ch_x, ch_ground = 540, 1590
    face = Face()
    props = {}
    # cara según el momento
    if t < 1.9:
        face = Face(mouth="talk", mouth_open=talk_amount(t), brow_raise=0.3)
    elif t < 2.8:
        face = Face(mouth="smile", look=(0.2, 0))
    elif t < 4.6:
        face = Face(mouth="smug", brow_raise=-0.2, look=(-0.4, 0.2))
    elif t < 5.0:
        face = Face(mouth="flat", brow_raise=0.6, look=(0, -1))
    elif t < 6.3:
        face = Face(mouth="o", brow_raise=1, eye_scale=1.3, look=(0, -1))
    else:
        face = Face(mouth="talk", mouth_open=talk_amount(t), brow_raise=0.8,
                    brow_tilt=1, look=(0, 0))
    if t < 2.8 or t >= 4.6:
        face.eye_open = blink_amount(t, seed=3)
    props["glasses"] = ease_out_back((t - 2.15) / 0.3) if t > 2.15 else 0
    props["mustache"] = ease_out_back((t - 2.4) / 0.3) if t > 2.4 else 0
    if t > 5.35:
        props["sweat"] = ease_out_back((t - 5.35) / 0.25)
    # salto
    lift, squash = 0.0, 0.0
    if 5.0 <= t < 5.25:
        squash = 0.12 * ((t - 5.0) / 0.25)
    elif 5.25 <= t < 5.75:
        u = (t - 5.25) / 0.5
        lift = 4 * 100 * u * (1 - u)
        squash = -0.10 * (1 - abs(2 * u - 1))
    elif 5.75 <= t < 6.1:
        u = (t - 5.75) / 0.35
        squash = 0.16 * math.exp(-5 * u) * math.cos(u * 9)
    pose = timeline.at(t)
    if 0.35 < t < 1.6:   # ola de la mano
        pose["ra_l"] += math.sin((t - 0.35) * 14) * 22
    ch = Character(x=ch_x, ground=ch_ground, scale=1.5, pose=pose, face=face,
                   props=props, lift=lift, squash=squash)
    for wx, wy, label, tin in WATCHERS:
        watcher(ctx, wx, wy, label, tin, t, (ch_x, ch_ground - 760 - lift))
    draw_character(ctx, ch, t=t, frame=frame)
    caption(ctx, t)
    subtitles(ctx, t)
    ctx.restore()


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else "demo_incognito.mp4"
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
    ctx = cairo.Context(surf)
    if out.endswith(".png"):
        render_frame(ctx, int(float(sys.argv[2]) * FPS))
        surf.write_to_png(out)
        return
    ff = subprocess.Popen(
        ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "bgra",
         "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-c:v", "libx264",
         "-pix_fmt", "yuv420p", "-crf", "18", "-preset", "medium", out],
        stdin=subprocess.PIPE)
    for f in range(int(DUR * FPS)):
        ctx.set_operator(cairo.OPERATOR_SOURCE)
        ctx.set_source_rgb(0, 0, 0)
        ctx.paint()
        ctx.set_operator(cairo.OPERATOR_OVER)
        render_frame(ctx, f)
        surf.flush()
        ff.stdin.write(bytes(surf.get_data()))
    ff.stdin.close()
    ff.wait()


if __name__ == "__main__":
    main()
