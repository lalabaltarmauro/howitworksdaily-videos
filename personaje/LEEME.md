# Personaje de palitos v2 — How It Works Daily

## Qué cambia respecto a los muñecos anteriores
- **Cuerpo articulado**: hombros, codos, caderas y rodillas. Brazos y piernas curvos "de goma", sin palitos rígidos.
- **Camiseta naranja de marca con mangas**: el personaje se reconoce de un vistazo y es siempre el mismo en todos los vídeos.
- **Cara expresiva**: ojos con brillo, parpadeo automático, cejas y 7 bocas (smile, grin, talk, o, frown, flat, smug).
- **Sincronía labial**: `talk_amount(t)` abre y cierra la boca mientras habla la voz.
- **Animación con peso**: transiciones suavizadas entre poses, anticipación (agacharse antes de saltar), squash & stretch al aterrizar y sombra que se encoge al saltar.
- **Respira** y tiene un ligero temblor de línea para parecer dibujado a mano.
- **Accesorios**: gafas, bigote, gota de sudor y signo de pregunta, cada uno con aparición "pop".

## Archivos
- `stickman.py`: el módulo del personaje. Es reutilizable en cualquier vídeo.
- `pose_sheet.py`: genera la hoja de poses en PNG.
- `demo_incognito.py`: la escena del gancho del vídeo de incógnito (8 s, 1080x1920, 30 fps). Sirve de plantilla de escena: título que salta, ojos que observan, subtítulos palabra a palabra y rebote de cámara.

## Requisitos
`pip install pycairo` y ffmpeg. Fuente Poppins Bold instalada.

## Uso básico
```python
from stickman import Character, Face, POSES, Timeline, draw_character, blink_amount, talk_amount
tl = Timeline([(0, POSES["idle"]), (0.4, POSES["wave"]), (2.0, POSES["point"])])
ch = Character(x=540, ground=1590, scale=1.5, pose=tl.at(t),
               face=Face(mouth="talk", mouth_open=talk_amount(t)))
ch.face.eye_open = blink_amount(t)
draw_character(ctx, ch, t=t, frame=frame)
```
Poses disponibles: idle, wave, point, hips, shrug, think, glasses, crouch, jump, surprised.
Para una pose nueva, añade un diccionario a `POSES`. Los ángulos están en grados: 0 = abajo, 90 = derecha, 180 = arriba.

## Pautas para cada vídeo
- Mismo personaje, misma camiseta y mismo fondo en todos los vídeos: es la marca del canal.
- Nunca dejar al personaje quieto: como mínimo, que hable, parpadee o respire.
- Cada 2-3 segundos, un cambio de pose o de expresión que acompañe a la frase.
- La reacción fuerte (salto, sorpresa) va justo en la revelación del mito.
