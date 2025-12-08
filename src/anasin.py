import sys

# Lista de tokens y posición actual (las usamos como "globales" para mantenerlo simple)
tokens = []
posicion = 0

def token_actual():
    global posicion, tokens
    if posicion < len(tokens):
        return tokens[posicion]
    else:
        return "EOF"

def avanzar():
    global posicion
    posicion += 1

def aceptar(esperado):
    """
    Si el token actual es 'esperado', avanza y regresa True.
    Si no, regresa False y no avanza.
    """
    if token_actual() == esperado:
        avanzar()
        return True
    return False

def esperar(esperado):
    """
    Igual que aceptar, pero si no coincide lanza un error sintáctico.
    """
    if not aceptar(esperado):
        mensaje = "se esperaba '{}' pero se encontró '{}'".format(
            esperado, token_actual()
        )
        raise Exception(mensaje)

# ------------ Reglas de la gramática ------------

# <PROG> → PROGRAMA [id] <SENTS> FINPROG
def PROG():
    esperar("PROGRAMA")
    esperar("[id]")
    SENTS(stop_tokens=["FINPROG"])
    esperar("FINPROG")

# <SENTS> → <SENT> <SENTS> | <SENT>
# Lo hacemos como: repetir <SENT> hasta encontrar un token de paro
def SENTS(stop_tokens):
    while True:
        t = token_actual()
        if t in stop_tokens or t == "EOF":
            break
        SENT()

# Selección del tipo de sentencia por el primer token
def SENT():
    t = token_actual()

    if t == "[id]":
        sent_asignacion()
    elif t == "SI":
        sent_si()
    elif t == "MIENTRAS":
        sent_mientras()
    elif t == "IMPRIME":
        sent_imprime()
    elif t == "LEE":
        sent_lee()
    # La gramática menciona: <SENT> → # [comentario],
    # pero en el .lex no se guardan comentarios, así que aquí no los vemos.
    else:
        raise Exception("sentencia desconocida que inicia con '{}'".format(t))

# <SENT> → [id] = <EXPR>
def sent_asignacion():
    esperar("[id]")
    esperar("=")
    EXPR()

# <SENT> → SI <COMPARA> ENTONCES <SENTS> SINO <SENTS> FINSI
# <SENT> → SI <COMPARA> ENTONCES <SENTS> FINSI
def sent_si():
    esperar("SI")
    COMPARA()
    esperar("ENTONCES")
    # bloque then
    SENTS(stop_tokens=["SINO", "FINSI"])
    # bloque else opcional
    if aceptar("SINO"):
        SENTS(stop_tokens=["FINSI"])
    esperar("FINSI")

# <SENT> → MIENTRAS <COMPARA> HACER <SENTS> FINM
def sent_mientras():
    esperar("MIENTRAS")
    COMPARA()
    esperar("HACER")
    SENTS(stop_tokens=["FINM"])
    esperar("FINM")

# <SENT> → IMPRIME <EXPR>
# <SENT> → IMPRIME [txt]
def sent_imprime():
    esperar("IMPRIME")
    # Puede ser texto literal...
    if aceptar("[txt]"):
        return
    # ...o una expresión
    EXPR()

# <SENT> → LEE [id]
def sent_lee():
    esperar("LEE")
    esperar("[id]")

# <EXPR> → <FAC> [op_ar] <FAC> | <FAC>
def EXPR():
    FAC()
    if aceptar("[op_ar]"):
        FAC()

# <FAC> → [id]
# <FAC> → [val]
def FAC():
    if aceptar("[id]"):
        return
    if aceptar("[val]"):
        return
    mensaje = "se esperaba [id] o [val] en expresión, se encontró '{}'".format(
        token_actual()
    )
    raise Exception(mensaje)

# <COMPARA> → [id] [op_rel] <EXPR>
def COMPARA():
    esperar("[id]")
    esperar("[op_rel]")
    EXPR()

# ------------ Función principal ------------

def main():
    global tokens, posicion

    if len(sys.argv) != 2:
        print("Uso: python anasin.py programa.lex")
        return

    nombre_lex = sys.argv[1]

    try:
        with open(nombre_lex, "r", encoding="utf-8") as f:
            lineas = f.readlines()
    except FileNotFoundError:
        print("No se pudo abrir el archivo:", nombre_lex)
        return

    # Cargar tokens del .lex (un token por línea)
    tokens = []
    for linea in lineas:
        tok = linea.strip()
        if tok != "":
            tokens.append(tok)

    # Empezar desde el primer token
    posicion = 0

    try:
        PROG()
        # Después de PROG ya no debe haber tokens extra
        if token_actual() != "EOF" and posicion != len(tokens):
            raise Exception("tokens extra después de FINPROG: '{}'".format(token_actual()))
        print("Compilación exitosa")
    except Exception as e:
        # Mensaje de error simple
        print("Error sintáctico:", e)
        print("Compilación no exitosa")

if __name__ == "__main__":
    # Agregamos un token EOF lógico al final al evaluar token_actual()
    main()