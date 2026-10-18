"""Hoja de poses y expresiones del personaje."""
import sys
import cairo
from stickman import Character, Face, POSES, draw_character

W, H = 1620, 1300
surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
ctx = cairo.Context(surf)
g = cairo.LinearGradient(0, 0, 0, H)
g.add_color_stop_rgb(0, 0.97, 0.95, 0.91)
g.add_color_stop_rgb(1, 0.92, 0.89, 0.83)
ctx.set_source(g)
ctx.paint()

cells = [
    ("Hablar", "idle", Face(mouth="talk", mouth_open=0.7)),
    ("Saludar", "wave", Face(mouth="grin", brow_raise=0.4)),
    ("Explicar", "point", Face(mouth="smile", look=(1, 0))),
    ("No sé", "shrug", Face(mouth="flat", brow_raise=0.6, brow_tilt=1)),
    ("Pensar", "think", Face(mouth="flat", look=(0.8, -1), brow_raise=0.3)),
    ("¡Sorpresa!", "surprised", Face(mouth="o", brow_raise=1, eye_scale=1.25)),
]
props = [{}, {}, {}, {"sweat": 1}, {"question": 1}, {"sweat": 1}]
for i, (label, pose, face) in enumerate(cells):
    cx = 270 + (i % 3) * 540
    gy = 560 + (i // 3) * 640
    ch = Character(x=cx, ground=gy, scale=0.82, pose=dict(POSES[pose]), face=face,
                   props=props[i], breathe=False)
    draw_character(ctx, ch, t=0, frame=i * 7)
    ctx.select_font_face("Poppins", 0, 1)
    ctx.set_font_size(38)
    ext = ctx.text_extents(label)
    ctx.move_to(cx - ext.width / 2 - ext.x_bearing, gy + 70)
    ctx.set_source_rgb(0.11, 0.11, 0.17)
    ctx.show_text(label)

surf.write_to_png(sys.argv[1] if len(sys.argv) > 1 else "pose_sheet.png")
