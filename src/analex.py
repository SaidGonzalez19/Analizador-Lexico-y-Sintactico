"""
ANALIZADOR LÉXICO PRO PARA MIO
-------------------------------------------------------------
Características:
- Acepta líneas vacías
- Acepta tabs, espacios, indentación variada
- Acepta comentarios al inicio o en mitad de línea
- Modo DEBUG activable desde variable global
- Errores léxicos con línea, columna y lexema
- Manejo seguro de BOM (archivos UTF-8 con BOM)
-------------------------------------------------------------
"""

DEBUG = False   # Cambiar a True si quieres ver tokens en consola

from dataclasses import dataclass
import os
import sys

RESERVED = {
    "PROGRAMA", "FINPROG",
    "SI", "ENTONCES", "SINO", "FINSI",
    "MIENTRAS", "HACER", "FINM",
    "IMPRIME", "LEE"
}

@dataclass
class Token:
    kind: str
    lexeme: str
    line: int
    col: int

class Lexer:
    def __init__(self, source: str):
        self.lines = source.splitlines()
        self.tokens = []
        self.errors = []
        self.ids = {}
        self.txts = {}
        self.vals = {}
        self.debug_output = []

    # -------------------------------------------------------
    def log(self, msg):
        if DEBUG:
            print(msg)
        self.debug_output.append(msg)

    # -------------------------------------------------------
    def run(self):
        for lineno, raw_line in enumerate(self.lines, start=1):
            line = raw_line.replace("\ufeff", "")  # eliminar BOM
            # cortar comentarios en mitad de línea
            if "#" in line:
                idx = line.index("#")
                line = line[:idx]

            stripped = line.strip()
            if stripped == "":
                continue

            self.tokenize_line(line, lineno)

    # -------------------------------------------------------
    def tokenize_line(self, line, lineno):
        i = 0
        n = len(line)

        while i < n:
            ch = line[i]

            # saltar whitespace interno
            if ch.isspace():
                i += 1
                continue

            col = i + 1

            # ---------------------------------------------------
            # LITERAL DE TEXTO
            # ---------------------------------------------------
            if ch == '"':
                j = i + 1
                literal = []
                while j < n and line[j] != '"':
                    literal.append(line[j])
                    j += 1
                if j >= n:
                    self.add_error("literal de texto sin cierre", lineno, col)
                    return
                txt = "".join(literal)
                if txt not in self.txts:
                    self.txts[txt] = f"TX{len(self.txts)+1:02d}"
                self.add_token("TXT", txt, lineno, col)
                i = j + 1
                continue

            # ---------------------------------------------------
            # IDENTIFICADOR O PALABRA RESERVADA
            # ---------------------------------------------------
            if ch.isalpha():
                j = i + 1
                while j < n and line[j].isalnum():
                    j += 1
                lex = line[i:j]
                if len(lex) > 16:
                    self.add_error(f"identificador demasiado largo: '{lex}'", lineno, col)
                    i = j
                    continue
                if lex in RESERVED:
                    self.add_token(lex, lex, lineno, col)
                else:
                    if lex not in self.ids:
                        self.ids[lex] = f"ID{len(self.ids)+1:02d}"
                    self.add_token("ID", lex, lineno, col)
                i = j
                continue

            # ---------------------------------------------------
            # NÚMERO HEXADECIMAL
            # ---------------------------------------------------
            if ch == "0" and i+1 < n and line[i+1] in ("x", "X"):
                j = i + 2
                while j < n and (line[j].isdigit() or line[j].upper() in "ABCDEF"):
                    j += 1
                lex = line[i:j]
                if len(lex) <= 2:
                    self.add_error("hexadecimal sin dígitos", lineno, col)
                else:
                    norm = "0x" + lex[2:].upper()
                    dec = int(norm[2:], 16)
                    if norm not in self.vals:
                        self.vals[norm] = (norm, dec)
                    self.add_token("VAL", norm, lineno, col)
                i = j
                continue

            # ---------------------------------------------------
            # OPERADORES RELACIONALES DOBLES
            # ---------------------------------------------------
            two = line[i:i+2]
            if two in ("<=", ">=", "<>", "=="):
                self.add_token("OP_REL", two, lineno, col)
                i += 2
                continue

            # ---------------------------------------------------
            # OPERADORES RELACIONALES SIMPLES
            # ---------------------------------------------------
            if ch in ("<", ">"):
                self.add_token("OP_REL", ch, lineno, col)
                i += 1
                continue

            # ---------------------------------------------------
            # ASIGNACIÓN
            # ---------------------------------------------------
            if ch == "=":
                self.add_token("ASIG", "=", lineno, col)
                i += 1
                continue

            # ---------------------------------------------------
            # OPERADORES ARITMÉTICOS
            # ---------------------------------------------------
            if ch in "+-*/":
                self.add_token("OP_AR", ch, lineno, col)
                i += 1
                continue

            # ---------------------------------------------------
            # CUALQUIER OTRA COSA = ERROR
            # ---------------------------------------------------
            self.add_error(f"carácter no reconocido '{ch}'", lineno, col)
            i += 1

    # -------------------------------------------------------
    def add_token(self, kind, lexeme, line, col):
        self.tokens.append(Token(kind, lexeme, line, col))
        self.log(f"[TOKEN] {kind} '{lexeme}' en línea {line}, col {col}")

    def add_error(self, msg, line, col):
        full = f"Error léxico: {msg} (línea {line}, col {col})"
        self.errors.append(full)
        self.log("[ERROR] " + full)

    # -------------------------------------------------------
    # SALIDA .LEX Y .SIM
    # -------------------------------------------------------
    def write_outputs(self, base):
        lex = base + ".lex"
        sim = base + ".sim"

        with open(lex, "w", encoding="utf-8") as f:
            for t in self.tokens:
                if t.kind == "ID": f.write("[id]\n")
                elif t.kind == "VAL": f.write("[val]\n")
                elif t.kind == "TXT": f.write("[txt]\n")
                elif t.kind == "OP_REL": f.write("[op_rel]\n")
                elif t.kind == "OP_AR": f.write("[op_ar]\n")
                elif t.kind == "ASIG": f.write("=\n")
                else: f.write(t.kind + "\n")

        with open(sim, "w", encoding="utf-8") as f:
            f.write("IDS\n")
            for name, code in self.ids.items():
                f.write(f"{name}, {code}\n")
            f.write("TXT\n")
            for txt, code in self.txts.items():
                f.write(f"\"{txt}\", {code}\n")
            f.write("VAL\n")
            for hexv, (norm, dec) in self.vals.items():
                f.write(f"{norm}, {dec}\n")

        if DEBUG:
            open(base + "_debug.log", "w").write("\n".join(self.debug_output))



def main():
    if len(sys.argv) != 1 and len(sys.argv) != 2:
        print("Uso: python analex.py archivo.mio")
        return

    src = sys.argv[1]
    base, _ = os.path.splitext(src)
    text = open(src, encoding="utf-8").read()

    L = Lexer(text)
    L.run()

    if L.errors:
        print("\n".join(L.errors))
        print("Análisis detenido por errores.")
        return

    L.write_outputs(base)
    print(f"Análisis léxico exitoso. Archivos generados: {base}.lex y {base}.sim")


if __name__ == "__main__":
    main()
