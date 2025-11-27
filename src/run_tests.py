"""
RUN TESTS AUTOMÁTICO PARA EL COMPILADOR MIO
--------------------------------------------
Este script:
- Busca todas las carpetas dentro de ../tests
- Toma todos los archivos .mio dentro de cada carpeta
- Ejecuta analex.py y anasin.py automáticamente
- Genera .lex, .sim y salida.log para cada prueba
- Muestra una tabla de resultados en consola
"""

import os
import subprocess
import sys
from pathlib import Path

# Ruta a la carpeta del proyecto (este archivo está en /src)
ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
TESTS = ROOT / "tests"

print("=============================================")
print("     RUNNING AUTOMATED TESTS FOR MIO")
print("=============================================\n")

if not TESTS.exists():
    print("No existe la carpeta /tests. Créala primero.")
    sys.exit(1)

analex_path = SRC / "analex.py"
anasin_path = SRC / "anasin.py"

if not analex_path.exists() or not anasin_path.exists():
    print("ERROR: analex.py o anasin.py no están en /src")
    sys.exit(1)

results = []

for folder in sorted(TESTS.iterdir()):
    if not folder.is_dir():
        continue

    # Buscar archivo .mio en la carpeta
    mio_files = list(folder.glob("*.mio"))
    if not mio_files:
        print(f"[WARN] {folder.name}: no hay archivo .mio, se omite.\n")
        continue

    mio = mio_files[0]
    base = mio.with_suffix("")

    print(f"📄 Probando: {folder.name}")
    print(f"    Archivo: {mio.name}")

    log_path = folder / "salida.log"
    with open(log_path, "w", encoding="utf-8") as log:

        # ------------------------------
        # 1. ANALIZADOR LÉXICO
        # ------------------------------
        cmd_lex = ["python", str(analex_path), str(mio)]
        p1 = subprocess.Popen(cmd_lex, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        lex_output, _ = p1.communicate()

        log.write("=== ANALISIS LEXICO ===\n")
        log.write(lex_output + "\n")

        lex_ok = "Análisis léxico exitoso" in lex_output

        # ------------------------------
        # 2. ANALIZADOR SINTÁCTICO (solo si lex fue OK)
        # ------------------------------
        sint_ok = False
        if lex_ok:
            lex_file = base.with_suffix(".lex")
            cmd_sin = ["python", str(anasin_path), str(lex_file)]

            p2 = subprocess.Popen(cmd_sin, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
            sin_output, _ = p2.communicate()

            log.write("\n=== ANALISIS SINTACTICO ===\n")
            log.write(sin_output + "\n")

            sint_ok = "Compilación exitosa" in sin_output

        # Guardar estado final
        results.append((folder.name, lex_ok, sint_ok))

    print("    ✔ LÉXICO OK" if lex_ok else "    ❌ Error LÉXICO")
    print("    ✔ SINTÁCTICO OK\n" if sint_ok else "    ❌ Error SINTÁCTICO\n")

print("=============================================")
print("                RESULTADOS")
print("=============================================")

for name, lex_ok, sin_ok in results:
    print(f"{name}: ", end="")
    if lex_ok:
        print("LEX=✔", end=" ")
    else:
        print("LEX=❌", end=" ")

    if sin_ok:
        print("SIN=✔")
    else:
        print("SIN=❌")

print("\nTodos los resultados fueron guardados en salida.log de cada prueba.\n")
