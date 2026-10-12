"""Renderiza `video/index.html` a MP4 (1080x1350, 30 fps, 30 s) con Chromium y ffmpeg.

    .venv/Scripts/python.exe video/render.py                 # el vídeo completo -> video/out/barcelona-2028.mp4
    .venv/Scripts/python.exe video/render.py --stills 5 12   # solo fotogramas sueltos (segundos) -> video/out/still_*.png

Necesita `playwright` (con Chromium) e `imageio-ffmpeg`, que trae el ejecutable de ffmpeg.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import imageio_ffmpeg
from playwright.sync_api import sync_playwright

RAIZ = Path(__file__).resolve().parents[1]
SALIDA = RAIZ / "video" / "out"
PUERTO = 8788
FPS = 30


def main() -> None:
    SALIDA.mkdir(parents=True, exist_ok=True)
    servidor = subprocess.Popen([sys.executable, "-m", "http.server", str(PUERTO), "--directory", str(RAIZ)],
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        with sync_playwright() as p:
            navegador = p.chromium.launch()
            pagina = navegador.new_page(viewport={"width": 1080, "height": 1350})
            pagina.goto(f"http://127.0.0.1:{PUERTO}/video/index.html?render=1")
            pagina.wait_for_function("window.ready === true", timeout=60000)
            duracion = pagina.evaluate("window.DURACION")

            if "--stills" in sys.argv:
                for s in sys.argv[sys.argv.index("--stills") + 1:]:
                    pagina.evaluate("t => window.draw(t)", float(s))
                    pagina.screenshot(path=str(SALIDA / f"still_{float(s):05.2f}.png"))
                    print("still", s)
            else:
                destino = SALIDA / "barcelona-2028.mp4"
                ff = subprocess.Popen([imageio_ffmpeg.get_ffmpeg_exe(), "-y", "-loglevel", "error", "-f", "image2pipe",
                                       "-framerate", str(FPS), "-i", "-", "-c:v", "libx264", "-pix_fmt", "yuv420p",
                                       "-crf", "16", "-preset", "slow", "-movflags", "+faststart", str(destino)],
                                      stdin=subprocess.PIPE)
                total = int(duracion * FPS)
                for f in range(total):
                    pagina.evaluate("t => window.draw(t)", f / FPS)
                    ff.stdin.write(pagina.screenshot(type="png"))
                    if f % 90 == 0:
                        print(f"  {f}/{total}", flush=True)
                ff.stdin.close()
                ff.wait()
                print("Guardado en", destino)
            navegador.close()
    finally:
        servidor.terminate()


if __name__ == "__main__":
    main()
