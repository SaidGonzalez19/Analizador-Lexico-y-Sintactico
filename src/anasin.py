"""
anasin.py - Analizador sintáctico para el lenguaje MIO.

Uso:
    python anasin.py programa.lex

Lee la secuencia de tokens del archivo .lex y verifica que
cumpla con la gramática dada en la práctica. Imprime:

    Compilación exitosa

si todo está bien, o un mensaje de error sintáctico en caso contrario.
"""

from dataclasses import dataclass
from typing import List
import sys
import os


@dataclass
class PToken:
    value: str  # token tal como aparece en el .lex (PROGRAMA, [id], etc.)
    pos: int    # índice en la secuencia (0-based)


class ParseError(Exception):
    pass


class Parser:
    def __init__(self, tokens: List[PToken]):
        self.tokens = tokens
        self.pos = 0

    # utilidades básicas -------------------------------------------------
    def current(self) -> PToken:
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return PToken("EOF", len(self.tokens))

    def accept(self, value: str) -> bool:
        if self.current().value == value:
            self.pos += 1
            return True
        return False

    def expect(self, value: str):
        if not self.accept(value):
            tok = self.current()
            raise ParseError(
                f"se esperaba '{value}' pero se encontró '{tok.value}' "
                f"en posición {tok.pos + 1}"
            )

    # punto de entrada ---------------------------------------------------
    def parse(self):
        self.PROG()
        if self.current().value != "EOF":
            raise ParseError(
                f"tokens extra después de FINPROG "
                f"(token '{self.current().value}' en posición {self.current().pos + 1})"
            )

    # Gramática ----------------------------------------------------------
    # <PROG> → PROGRAMA [id] <SENTS> FINPROG
    def PROG(self):
        self.expect("PROGRAMA")
        self.expect("[id]")
        self.SENTS(stop_tokens={"FINPROG"})
        self.expect("FINPROG")

    # <SENTS> → <SENT> <SENTS> | <SENT>
    # Implementado como: cero o más <SENT> hasta encontrar un token de parada
    def SENTS(self, stop_tokens: set):
        while self.current().value not in stop_tokens and self.current().value != "EOF":
            self.SENT()

    # Selección de tipo de sentencia por el primer token
    def SENT(self):
        tok = self.current()
        if tok.value == "[id]":
            self.sent_asignacion()
        elif tok.value == "SI":
            self.sent_si()
        elif tok.value == "MIENTRAS":
            self.sent_mientras()
        elif tok.value == "IMPRIME":
            self.sent_imprime()
        elif tok.value == "LEE":
            self.sent_lee()
        else:
            raise ParseError(
                f"sentencia desconocida que inicia con '{tok.value}' "
                f"en posición {tok.pos + 1}"
            )

    # [id] = <EXPR>
    def sent_asignacion(self):
        inicio = self.current().pos
        try:
            self.expect("[id]")
            self.expect("=")
            self.EXPR()
        except ParseError as e:
            raise ParseError(f"Error en sentencia de asignación (posición {inicio + 1}): {e}")

    # SI <COMPARA> ENTONCES <SENTS> SINO <SENTS> FINSI
    # SI <COMPARA> ENTONCES <SENTS> FINSI
    def sent_si(self):
        inicio = self.current().pos
        try:
            self.expect("SI")
            self.COMPARA()
            self.expect("ENTONCES")
            # bloque "then"
            self.SENTS(stop_tokens={"SINO", "FINSI"})
            # bloque opcional "else"
            if self.accept("SINO"):
                self.SENTS(stop_tokens={"FINSI"})
            self.expect("FINSI")
        except ParseError as e:
            raise ParseError(f"Error en sentencia SI (posición {inicio + 1}): {e}")

    # MIENTRAS <COMPARA> HACER <SENTS> FINM
    def sent_mientras(self):
        inicio = self.current().pos
        try:
            self.expect("MIENTRAS")
            self.COMPARA()
            self.expect("HACER")
            self.SENTS(stop_tokens={"FINM"})
            self.expect("FINM")
        except ParseError as e:
            raise ParseError(f"Error en sentencia MIENTRAS (posición {inicio + 1}): {e}")

    # IMPRIME <EXPR> | IMPRIME [txt]
    def sent_imprime(self):
        inicio = self.current().pos
        try:
            self.expect("IMPRIME")
            # puede ser texto literal...
            if self.accept("[txt]"):
                return
            # ...o una expresión
            self.EXPR()
        except ParseError as e:
            raise ParseError(f"Error en sentencia IMPRIME (posición {inicio + 1}): {e}")

    # LEE [id]
    def sent_lee(self):
        inicio = self.current().pos
        try:
            self.expect("LEE")
            self.expect("[id]")
        except ParseError as e:
            raise ParseError(f"Error en sentencia LEE (posición {inicio + 1}): {e}")

    # <EXPR> → <FAC> [op_ar] <FAC>|<FAC>
    def EXPR(self):
        self.FAC()
        if self.accept("[op_ar]"):
            self.FAC()

    # <FAC> → [id] | [val]
    def FAC(self):
        if self.accept("[id]"):
            return
        if self.accept("[val]"):
            return
        raise ParseError(
            f"se esperaba [id] o [val] en expresión, se encontró "
            f"'{self.current().value}' en posición {self.current().pos + 1}"
        )

    # <COMPARA> → [id] [op_rel] <EXPR>
    def COMPARA(self):
        self.expect("[id]")
        self.expect("[op_rel]")
        self.EXPR()


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]

    if len(argv) != 1:
        print("Uso: python anasin.py <archivo.lex>")
        raise SystemExit(1)

    lex_path = argv[0]
    if not os.path.isfile(lex_path):
        print(f"No se encontró el archivo: {lex_path}")
        raise SystemExit(1)

    with open(lex_path, "r", encoding="utf-8") as f:
        text = f.read()

    tokens: List[PToken] = []
    for line in text.splitlines():
        tok = line.strip()
        if not tok:
            continue
        tokens.append(PToken(tok, len(tokens)))
    tokens.append(PToken("EOF", len(tokens)))

    parser = Parser(tokens)
    try:
        parser.parse()
        print("Compilación exitosa")
    except ParseError as e:
        print(f"Error sintáctico: {e}")


if __name__ == "__main__":
    main()
