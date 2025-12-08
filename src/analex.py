import sys

# Palabras reservadas del lenguaje MIO (de la hoja del proyecto)
RESERVADAS = [
    "PROGRAMA", "FINPROG",
    "SI", "ENTONCES", "SINO", "FINSI",
    "MIENTRAS", "HACER", "FINM",
    "IMPRIME", "LEE"
]

def es_letra(c):
    return ('a' <= c <= 'z') or ('A' <= c <= 'Z')

def es_digito(c):
    return '0' <= c <= '9'

def es_hex(c):
    c = c.upper()
    return ('0' <= c <= '9') or ('A' <= c <= 'F')

def procesar_linea(linea, num_linea, tokens, ids, txts, vals, errores):
    """
    Analiza una línea de texto y agrega tokens o errores a las listas.
    """
    i = 0
    n = len(linea)

    # Ignorar línea si es comentario (# al inicio) o está vacía
    linea_sin_espacios = linea.lstrip()
    if linea_sin_espacios == "" or linea_sin_espacios.startswith("#"):
        return

    while i < n:
        c = linea[i]

        # Saltar espacios y tabs
        if c.isspace():
            i += 1
            continue

        # Literales de texto: " ... "
        if c == '"':
            inicio_col = i + 1
            i += 1
            texto = ""
            while i < n and linea[i] != '"':
                texto += linea[i]
                i += 1
            if i >= n:
                errores.append("Error léxico en línea {}: literal de texto sin cierre".format(num_linea))
                return
            # Saltar la comilla de cierre
            i += 1

            # Guardar en tabla TXT si es nuevo
            if texto not in txts:
                indice = len(txts) + 1
                codigo = "TX{:02d}".format(indice)
                txts[texto] = codigo

            tokens.append("[txt]")
            continue

        # Palabras: pueden ser reservadas o identificadores
        if es_letra(c):
            inicio = i
            while i < n and (es_letra(linea[i]) or es_digito(linea[i])):
                i += 1
            lexema = linea[inicio:i]

            # Reservada o identificador
            if lexema in RESERVADAS:
                tokens.append(lexema)
            else:
                # Verificar longitud de identificador (máx 16)
                if len(lexema) > 16:
                    errores.append(
                        "Error léxico en línea {}: identificador demasiado largo '{}'".format(num_linea, lexema)
                    )
                    # seguimos analizando la línea
                    continue

                # Guardar en tabla IDS si es nuevo
                if lexema not in ids:
                    indice = len(ids) + 1
                    codigo = "ID{:02d}".format(indice)
                    ids[lexema] = codigo

                tokens.append("[id]")
            continue

        # Literales numéricas hexadecimales: 0x...
        if c == '0' and i + 1 < n and linea[i + 1] == 'x':
            inicio = i
            i += 2  # saltar '0x'
            if i >= n or not es_hex(linea[i]):
                errores.append("Error léxico en línea {}: literal hexadecimal sin dígitos".format(num_linea))
                return

            while i < n and es_hex(linea[i]):
                i += 1

            lexema = linea[inicio:i]  # por ejemplo "0x1" o "0xA"
            # Guardar en tabla VAL si es nuevo
            if lexema not in vals:
                valor_decimal = int(lexema[2:], 16)
                vals[lexema] = valor_decimal
            tokens.append("[val]")
            continue

        # Operadores relacionales: >=, <=, <>, >, <, ==
        if c == '<' or c == '>':
            if i + 1 < n:
                dos = c + linea[i + 1]
                if dos == "<=" or dos == ">=" or dos == "<>":
                    tokens.append("[op_rel]")
                    i += 2
                    continue
            # Si no fue doble, es simple < o >
            tokens.append("[op_rel]")
            i += 1
            continue

        # '=' puede ser asignación o parte de '=='
        if c == '=':
            if i + 1 < n and linea[i + 1] == '=':
                tokens.append("[op_rel]")  # ==
                i += 2
            else:
                tokens.append("=")  # asignación
                i += 1
            continue

        # Operadores aritméticos: + - * /
        if c in ['+', '-', '*', '/']:
            tokens.append("[op_ar]")
            i += 1
            continue

        # Si llegamos aquí, el carácter no es válido en el lenguaje
        errores.append(
            "Error léxico en línea {}: carácter no reconocido '{}'".format(num_linea, c)
        )
        i += 1  # avanzar para no quedarse atorado

def escribir_archivos(base, tokens, ids, txts, vals):
    """
    Escribe los archivos base.lex y base.sim
    """
    nombre_lex = base + ".lex"
    nombre_sim = base + ".sim"

    # .lex: un token por línea en el orden que se detectaron
    with open(nombre_lex, "w", encoding="utf-8") as f:
        for t in tokens:
            f.write(t + "\n")

    # .sim: IDS, TXT, VAL en ese orden, como en el ejemplo del PDF
    with open(nombre_sim, "w", encoding="utf-8") as f:
        f.write("IDS\n")
        for nombre, codigo in ids.items():
            f.write("{}, {}\n".format(nombre, codigo))

        f.write("TXT\n")
        for texto, codigo in txts.items():
            f.write("\"{}\", {}\n".format(texto, codigo))

        f.write("VAL\n")
        for lexema_hex, dec in vals.items():
            f.write("{}, {}\n".format(lexema_hex, dec))

def main():
    if len(sys.argv) != 2:
        print("Uso: python analex.py programa.mio")
        return

    nombre_archivo = sys.argv[1]

    # Sacar el nombre base para .lex y .sim (por ejemplo "factorial" de "factorial.mio")
    if nombre_archivo.endswith(".mio"):
        base = nombre_archivo[:-4]
    else:
        base = nombre_archivo

    try:
        with open(nombre_archivo, "r", encoding="utf-8") as f:
            lineas = f.readlines()
    except FileNotFoundError:
        print("No se pudo abrir el archivo:", nombre_archivo)
        return

    tokens = []
    ids = {}   # nombre -> IDxx
    txts = {}  # texto -> TXxx
    vals = {}  # "0x.." -> valor decimal
    errores = []

    # Analizar línea por línea
    num_linea = 1
    for linea in lineas:
        procesar_linea(linea.rstrip("\n"), num_linea, tokens, ids, txts, vals, errores)
        num_linea += 1

    # Revisar si hubo errores
    if len(errores) > 0:
        for e in errores:
            print(e)
        print("Análisis léxico no exitoso.")
        return

    # Si no hubo errores, escribir archivos .lex y .sim
    escribir_archivos(base, tokens, ids, txts, vals)
    print("Análisis léxico exitoso.")
    print("Se generaron los archivos {}.lex y {}.sim".format(base, base))

if __name__ == "__main__":
    main()