#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Aparato semántico de Nivel 6 para el repositorio de perfil.

Este repositorio no tiene motor numérico: su único objeto medible es la PROMESA
que el README le hace al lector. El aparato sustituye «los ficheros existen y
compilan» (`.github/verify_manifest.py`, retirado) por paridad verificable entre
lo que el README **declara** y lo que el README **contiene**:

  1. Cuerpo y huellas — el README existe, pasa de 50 líneas y lleva sus marcas.
  2. Cifra declarada = filas medidas, en los DOS inventarios:
       · «## Start here — ten repositories» declara DIEZ y su tabla tiene 10 filas;
       · la huella `HUELLA-PERFIL-FISICA-7-INSTRUMENTOS` declara SIETE y la tabla
         de `## Origin` tiene 7 filas.
     La cifra se LEE del texto: mover una fila sin mover su declaración es rojo.
  3. Numeración contigua `1..N`: una fila duplicada o saltada rompe la promesa.
  4. Censo — ningún `alexisromtz-lab/<slug>` citado cae fuera del censo público
     del namespace. Atrapa el enlace a un repositorio que no existe, que es
     justo el error que un 404 no avisa en CI.
  5. Agotamiento — lo citado en prosa es exactamente la unión de los dos
     inventarios: una mención suelta sin fila es una promesa sin portador.
  6. Enlaces absolutos — cero rutas relativas (un perfil de GitHub no resuelve
     rutas relativas) y cero enlaces al namespace sin repositorio.

CENSO: de dónde sale y por qué NO es una constante. El censo se LEE de la captura
firmada que produce `tools/medir_censo.py --aplicar` (`censo_medido.json`: fecha,
comando y lista de repositorios públicos). Una lista congelada en este archivo no
puede diferir, y lo que no puede diferir no es evidencia: la de 2026-10-30 envejeció
a 23 repositorios y el rojo culpó al README de un enlace que sí existía — el defecto
estaba en el instrumento, no en el objeto. Una captura ausente o ilegible NO se lee
como censo vacío: se publica `CENSO_NO_MEDIDO` y enrojece con su causa (fail-closed).
El invariante sigue siendo de dirección única, `citado ⊆ censo`: un repositorio
público NUEVO no rompe el perfil; un enlace a uno inexistente sí.

Falsadores (lo que hace rojo a este banco; cada uno se ejercita abajo sobre una
copia mutada del README, por el MISMO código de producción, no sobre una
constante):

  · inyectar una fila con un repositorio fantasma      -> REPO_HUERFANO
  · añadir un octavo instrumento sin mover la huella   -> CIFRA_NO_CASA
  · duplicar el número de una fila                     -> NUMERACION_ROTA
  · colgar un enlace relativo                          -> ENLACE_RELATIVO
  · citar un repositorio solo en prosa, sin fila        -> INVENTARIO_DESALINEADO
"""

# HUELLA-TEST-PARIDAD-PERFIL-NV6-20261022

from __future__ import annotations

import json
import re
import urllib.parse
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
README = RAIZ / "README.md"

# HUELLA-CENSO-CAPTURA-FIRMADA-20261106
CENSO_CAPTURA = RAIZ / "censo_medido.json"


def _leer_censo(ruta: Path = CENSO_CAPTURA) -> tuple[str, str, frozenset[str], str]:
    """(fecha, comando, repositorios, error). Error vacío = censo medido."""
    if not ruta.is_file():
        return "", "", frozenset(), f"captura ausente: {ruta.name}"
    try:
        datos = json.loads(ruta.read_text(encoding="utf-8"))
    except ValueError as exc:  # JSON ilegible es un dato, no un accidente
        return "", "", frozenset(), f"{ruta.name} no es JSON: {exc}"
    if not isinstance(datos, dict):
        return "", "", frozenset(), f"{ruta.name} no declara un objeto"
    publicos = datos.get("publicos")
    if not isinstance(publicos, list) or not publicos:
        return "", "", frozenset(), f"{ruta.name} no declara repositorios públicos"
    return (
        str(datos.get("medido_en", "")),
        str(datos.get("comando", "")),
        frozenset(str(x) for x in publicos),
        "",
    )


CENSO_MEDIDO, CENSO_COMANDO, CENSO_PUBLICO, CENSO_ERROR = _leer_censo()

SECCION_INICIO = "## Start here"
SECCION_ORIGEN = "## Origin"
SECCION_PRODUCTOS = "## What we ship"
MIN_LINEAS = 50
MIN_HUELLAS = 3

PALABRA_A_NUMERO = {
    "four": 4,
    "five": 5,
    "six": 6,
    "seven": 7,
    "eight": 8,
    "nine": 9,
    "ten": 10,
    "cuatro": 4,
    "cinco": 5,
    "seis": 6,
    "siete": 7,
    "ocho": 8,
    "nueve": 9,
    "diez": 10,
}

RE_SLUG = re.compile(r"alexisromtz-lab/([A-Za-z0-9_.-]+)")
RE_HUELLA_INSTRUMENTOS = re.compile(r"HUELLA-[A-Z0-9-]*FISICA-(\d+)-INSTRUMENTOS")
RE_ENLACE = re.compile(r"\]\(([^)\s]+)\)")
# La raíz del namespace es un destino legítimo (la portada de la organización);
# lo que no se admite es un segmento de repositorio vacío o torcido.
RE_ENLACE_NAMESPACE = re.compile(
    r"^https://github\.com/alexisromtz-lab(/[A-Za-z0-9_.-]+(/.*)?)?/?$"
)


# --------------------------------------------------------------------- lectura
def texto(ruta: Path = README) -> str:
    """El README como texto. Una ruta inexistente no es un cero: es un fallo."""
    if not ruta.is_file():
        raise AssertionError(f"README_AUSENTE: {ruta} no existe")
    return ruta.read_text(encoding="utf-8")


def seccion(t: str, prefijo: str) -> str:
    """Cuerpo de la sección cuyo encabezado empieza por `prefijo`, sin el siguiente `## `."""
    inicio = t.find(prefijo)
    if inicio < 0:
        raise AssertionError(f"SECCION_AUSENTE: el README no declara {prefijo!r}")
    resto = t[inicio + len(prefijo) :]
    siguiente = re.search(r"^## ", resto, re.M)
    return resto if siguiente is None else resto[: siguiente.start()]


def filas(bloque: str) -> list[list[str]]:
    """Filas de DATOS de la tabla del bloque (cabecera y separador fuera)."""
    crudas = [l.strip() for l in bloque.splitlines() if l.lstrip().startswith("|")]
    if len(crudas) < 3:
        return []
    salida: list[list[str]] = []
    for linea in crudas[2:]:
        celdas = [c.strip() for c in linea.strip().strip("|").split("|")]
        if celdas and celdas[0]:
            salida.append(celdas)
    return salida


def slugs(t: str) -> set[str]:
    return set(RE_SLUG.findall(t))


def numeros(filas_: list[list[str]]) -> list[int]:
    return [int(f[0]) for f in filas_ if re.fullmatch(r"\d+", f[0])]


def _declarado_en_titulo(bloque: str) -> int | None:
    """La cifra que el propio encabezado declara, leída de su palabra."""
    lineas = bloque.splitlines()
    titulo = lineas[0] if lineas else ""
    for palabra, numero in PALABRA_A_NUMERO.items():
        if re.search(rf"\b{palabra}\b", titulo, re.I):
            return numero
    return None


# --------------------------------------------------------------------- auditor
def auditar(t: str) -> list[str]:
    """Todas las violaciones del contrato del perfil. Lista vacía = contrato cumplido."""
    v: list[str] = []

    if CENSO_ERROR:
        v.append(f"CENSO_NO_MEDIDO: {CENSO_ERROR}")

    lineas = len(t.splitlines())
    if lineas < MIN_LINEAS:
        v.append(f"README_VACIO: {lineas} líneas < {MIN_LINEAS}")
    huellas = t.count("HUELLA-")
    if huellas < MIN_HUELLAS:
        v.append(f"HUELLA_AUSENTE: {huellas} marcas < {MIN_HUELLAS}")

    ini = seccion(t, SECCION_INICIO)
    ori = seccion(t, SECCION_ORIGEN)
    filas_ini = filas(ini)
    filas_ori = filas(ori)

    declarado_ini = _declarado_en_titulo(ini)
    if declarado_ini is None:
        v.append("CIFRA_NO_DECLARADA: el título de «Start here» no dice cuántos repositorios")
    elif declarado_ini != len(filas_ini):
        v.append(
            f"CIFRA_NO_CASA: Start here declara {declarado_ini} y la tabla tiene "
            f"{len(filas_ini)} filas"
        )

    huella = RE_HUELLA_INSTRUMENTOS.search(t)
    if huella is None:
        v.append("CIFRA_NO_DECLARADA: falta la huella de N instrumentos")
    elif int(huella.group(1)) != len(filas_ori):
        v.append(
            f"CIFRA_NO_CASA: la huella declara {int(huella.group(1))} instrumentos y "
            f"la tabla de Origin tiene {len(filas_ori)} filas"
        )

    medidos = numeros(filas_ini)
    if medidos != list(range(1, len(filas_ini) + 1)):
        v.append(f"NUMERACION_ROTA: {medidos} != 1..{len(filas_ini)}")

    citados = slugs(t)
    huerfanos = sorted(citados - CENSO_PUBLICO)
    if huerfanos:
        v.append(
            f"REPO_HUERFANO: {huerfanos} no están en el censo público de {CENSO_MEDIDO}"
        )

    inventario = slugs(ini) | slugs(ori)
    sueltos = sorted(citados - inventario)
    if sueltos:
        v.append(
            f"INVENTARIO_DESALINEADO: {sueltos} se citan sin fila en ningún inventario"
        )

    for destino in RE_ENLACE.findall(t):
        if not destino.startswith(("http://", "https://", "mailto:", "#")):
            v.append(
                f"ENLACE_RELATIVO: {destino!r} (un perfil no resuelve rutas relativas)"
            )
        elif "github.com/alexisromtz-lab" in destino and not RE_ENLACE_NAMESPACE.match(
            destino
        ):
            v.append(f"ENLACE_MALFORMADO: {destino!r} apunta al namespace sin repositorio")
    return v


def violaciones(clase: str, t: str) -> list[str]:
    """Solo las violaciones de una clase: el diagnóstico nombra el defecto, no el total."""
    return [x for x in auditar(t) if x.startswith(clase)]


# ------------------------------------------------------------- bloque de precio
# El precio es el único campo comercial que este README publica, y por eso es el
# único que puede contradecir a la página viva. Medido el 2026-11-06 con
#   curl -s https://studiocity.app/ | grep -o '\$[0-9,]*/mes'
#   → Básico $499 · Pro $799 · Ilimitado $1,199 · tira de lanzamiento $249 (primer mes)
# La escalera que este contrato exigía antes ($299 · $599 · $899 «Premium») es el
# objeto de la captura 2026-11-01: el sitio la movió y el README la seguía publicando.
# La captura firmada (`precio_medido.json`, `tools/medir_precio.py --aplicar`) es la
# única vía para mover una cifra; este archivo coteja README ↔ captura, y
# `--check` coteja captura ↔ sitio. Un número que nadie volvió a medir no es cifra.
# <!-- HUELLA-PERFIL-PRECIO-CLAUSULA-NORMALIZADA-20261106 -->
# Adenda: los literales se buscan sobre el bloque con el espaciado colapsado — el
# README envuelve párrafos a ~100 columnas y un instrumento que enrojece por el ancho
# de línea no mide el sujeto. La cláusula cambió de signo: la condición de lanzamiento
# antes NO estaba publicada en el sitio ($99) y publicarla era el defecto; ahora SÍ lo
# está ($249, *Lanzamiento · primer mes*), así que el contrato ya no la prohíbe: exige
# que viaje pegada a su cláusula y dentro del bloque medido.
HUELLA_PRECIO = "HUELLA-PERFIL-PRECIO-MEDIDO-20261106"
PRECIO_ENTRADA = "$499/mes"
FECHA_PRECIO = "2026-11-06"
PLANES = ("Básico", "Pro", "Ilimitado")
LANZAMIENTO = "$249/mes"
CLAUSULA_LANZAMIENTO = "is published on the site"
FUENTE_PRECIO = "https://studiocity.app/"
COMANDO_PRECIO = "tools/medir_precio.py --check"
RE_CLAUSULA = re.compile(r"is\s+published\s+on\s+the\s+site")
RE_LANZAMIENTO = re.compile(r"\$ ?249(?!\d)")


def bloque_precio(t: str) -> str:
    """Desde la huella del precio hasta el siguiente encabezado de nivel 2."""
    i = t.find(HUELLA_PRECIO)
    if i < 0:
        return ""
    resto = t[i:]
    m = re.search(r"^## ", resto, re.M)
    return resto if m is None else resto[: m.start()]


def _compacto(s: str) -> str:
    """Colapsa el espaciado: un párrafo envuelto no cambia lo que el bloque declara."""
    return " ".join(s.split())


def auditar_precio(t: str) -> list[str]:
    """Contrato del único campo comercial: cifra, fecha, comando, sujeto y cláusula."""
    i = t.find(HUELLA_PRECIO)
    if i < 0:
        return [f"PRECIO_SIN_HUELLA: falta {HUELLA_PRECIO}"]
    bloque = bloque_precio(t)
    fin = i + len(bloque)
    visto = _compacto(bloque)
    v: list[str] = []
    if PRECIO_ENTRADA not in visto:
        v.append(f"PRECIO_NO_CASA: el bloque no publica {PRECIO_ENTRADA!r}")
    if FECHA_PRECIO not in visto:
        v.append("PRECIO_SIN_FECHA: el bloque no fecha su medición")
    if "curl" not in visto:
        v.append("PRECIO_SIN_COMANDO: el bloque no publica el comando que lo mide")
    if FUENTE_PRECIO not in visto:
        v.append(f"PRECIO_SIN_SUJETO: el bloque no nombra la fuente medida {FUENTE_PRECIO!r}")
    if CLAUSULA_LANZAMIENTO not in visto:
        v.append(f"PRECIO_SIN_CLAUSULA: el bloque no declara {CLAUSULA_LANZAMIENTO!r}")
    if COMANDO_PRECIO not in visto:
        v.append(
            f"PRECIO_SIN_INSTRUMENTO: el bloque no publica el comando que lo coteja "
            f"{COMANDO_PRECIO!r}"
        )
    for plan in PLANES:
        if plan not in visto:
            v.append(f"PRECIO_SIN_PLAN: el bloque no publica el plan {plan!r}")
    for m in RE_LANZAMIENTO.finditer(t):
        if not i <= m.start() < fin:
            v.append(f"PRECIO_SIN_CLAUSULA: `$249` fuera del bloque medido (offset {m.start()})")
    return v


def violaciones_precio(clase: str, t: str) -> list[str]:
    return [x for x in auditar_precio(t) if x.startswith(clase)]



# -------------------------------------------------------------------- mutación
def _anexar_fila(t: str, prefijo: str, fila: str) -> str:
    bloque = seccion(t, prefijo)
    return t.replace(bloque, bloque.rstrip("\n") + "\n" + fila + "\n", 1)


def _sustituir_en(t: str, prefijo: str, viejo: str, nuevo: str) -> str:
    bloque = seccion(t, prefijo)
    assert viejo in bloque, f"la mutación no aplica: {viejo!r} no está en {prefijo!r}"
    return t.replace(bloque, bloque.replace(viejo, nuevo, 1), 1)


# ------------------------------------------------------------------ invariantes
def test_el_readme_tiene_cuerpo_y_huellas():
    t = texto()
    assert not violaciones("README_VACIO", t), violaciones("README_VACIO", t)
    assert not violaciones("HUELLA_AUSENTE", t), violaciones("HUELLA_AUSENTE", t)


def test_el_inventario_de_inicio_casa_con_su_titulo():
    t = texto()
    assert not violaciones("CIFRA_NO_DECLARADA", t), violaciones("CIFRA_NO_DECLARADA", t)
    fallos = [x for x in violaciones("CIFRA_NO_CASA", t) if "Start here" in x]
    assert not fallos, fallos


def test_el_inventario_de_instrumentos_casa_con_su_huella():
    t = texto()
    fallos = [x for x in violaciones("CIFRA_NO_CASA", t) if "huella" in x]
    assert not fallos, fallos
    assert len(filas(seccion(t, SECCION_ORIGEN))) > 0, "VACUIDAD: Origin sin filas"


def test_las_filas_de_inicio_estan_numeradas_sin_huecos():
    t = texto()
    assert not violaciones("NUMERACION_ROTA", t), violaciones("NUMERACION_ROTA", t)


def test_ningun_repositorio_citado_es_huerfano_del_censo():
    t = texto()
    assert not violaciones("CENSO_NO_MEDIDO", t), violaciones("CENSO_NO_MEDIDO", t)
    assert not violaciones("REPO_HUERFANO", t), violaciones("REPO_HUERFANO", t)
    assert CENSO_COMANDO.strip(), "el censo tiene que declarar cómo se midió"
    assert CENSO_MEDIDO.strip(), "el censo tiene que declarar cuándo se midió"
    assert len(CENSO_PUBLICO) >= 19, len(CENSO_PUBLICO)


def test_los_dos_inventarios_agotan_lo_citado():
    t = texto()
    assert not violaciones("INVENTARIO_DESALINEADO", t), violaciones(
        "INVENTARIO_DESALINEADO", t
    )


def test_todos_los_enlaces_son_absolutos_y_bien_formados():
    t = texto()
    for clase in ("ENLACE_RELATIVO", "ENLACE_MALFORMADO"):
        assert not violaciones(clase, t), violaciones(clase, t)


def test_el_perfil_no_tiene_ninguna_violacion():
    """El contrato entero, de una pieza: si algo deriva, esto lo dice sin ambigüedad."""
    assert auditar(texto()) == []


# -------------------------------------------------------------------- falsadores
def test_falsador_repositorio_fantasma():
    fantasma = (
        "| 7 | [`repo-fantasma-2026`](https://github.com/alexisromtz-lab/repo-fantasma-2026)"
        " | no existe |"
    )
    mutado = _anexar_fila(texto(), SECCION_INICIO, fantasma)
    assert violaciones("REPO_HUERFANO", mutado), "el auditor no caza el repositorio fantasma"
    assert "repo-fantasma-2026" in " ".join(violaciones("REPO_HUERFANO", mutado))


def test_falsador_cifra_inflada():
    """Un octavo instrumento REAL en el censo: no es huérfano, es una cifra que no casa."""
    octavo = (
        "| [`auditor-toolkit`](https://github.com/alexisromtz-lab/auditor-toolkit)"
        " | no declarado en la huella | sin cifra |"
    )
    mutado = _anexar_fila(texto(), SECCION_ORIGEN, octavo)
    assert not violaciones("REPO_HUERFANO", mutado), "el control no aísla la cifra"
    assert violaciones("CIFRA_NO_CASA", mutado), "el auditor aceptó un inventario inflado"


def test_falsador_numeracion_duplicada():
    mutado = _sustituir_en(texto(), SECCION_INICIO, "| 2 |", "| 1 |")
    assert violaciones("NUMERACION_ROTA", mutado), "el auditor aceptó un número duplicado"


def test_falsador_enlace_relativo():
    mutado = texto() + "\n[roto](./NO_EXISTE_20261022.md)\n"
    assert violaciones("ENLACE_RELATIVO", mutado), "el auditor aceptó una ruta relativa"


def test_falsador_enlace_al_namespace_sin_repositorio():
    mutado = texto() + "\n[torcido](https://github.com/alexisromtz-lab//fantasma)\n"
    assert violaciones("ENLACE_MALFORMADO", mutado), "el auditor aceptó un segmento vacío"


def test_falsador_mencion_suelta_sin_fila():
    mutado = texto() + "\nVer también [`qnm`](https://github.com/alexisromtz-lab/qnm).\n"
    assert not violaciones("REPO_HUERFANO", mutado), "qnm sí está en el censo"
    assert violaciones("INVENTARIO_DESALINEADO", mutado), (
        "el auditor aceptó una mención sin fila de inventario"
    )


def test_el_auditor_lee_el_archivo_que_se_le_da(tmp_path):
    """El camino del fichero es real: una copia mutada en disco no puede dar verde."""
    fantasma = (
        "| 7 | [`fantasma`](https://github.com/alexisromtz-lab/fantasma) | x |"
    )
    copia = tmp_path / "README.md"
    copia.write_text(_anexar_fila(texto(), SECCION_INICIO, fantasma), encoding="utf-8")
    assert auditar(texto()) == []
    assert violaciones("REPO_HUERFANO", texto(copia)), "el auditor ignoró la ruta recibida"


# ------------------------------------------------------- invariantes del precio
def test_el_precio_publicado_lleva_su_medicion():
    t = texto()
    assert auditar_precio(t) == [], auditar_precio(t)


def test_el_precio_de_entrada_es_el_que_publica_el_sitio():
    """La cifra que este README vende no puede diferir de la que cobra la página."""
    bloque = bloque_precio(texto())
    assert PRECIO_ENTRADA in bloque, f"el bloque no publica {PRECIO_ENTRADA!r}"
    for plan in PLANES:
        assert plan in bloque, f"el bloque no publica el plan {plan!r}"
    assert LANZAMIENTO in bloque, f"el bloque no publica el lanzamiento {LANZAMIENTO!r}"


def test_falsador_lanzamiento_vendido_fuera_del_bloque():
    """El control que el CEO pidió: publicar `$249` como precio tiene que doler."""
    mutado = _sustituir_en(
        texto(), SECCION_PRODUCTOS, "| **Studio City**", "| `$249/mes` · **Studio City**"
    )
    assert not violaciones_precio("PRECIO_NO_CASA", mutado), "el control no aísla la cláusula"
    assert violaciones_precio("PRECIO_SIN_CLAUSULA", mutado), "el auditor aceptó un `$249` de oferta"


def test_falsador_precio_sin_comando():
    t = texto()
    bloque = bloque_precio(t)
    mutado = t.replace(bloque, bloque.replace("curl", "la página"), 1)
    assert "PRECIO_SIN_COMANDO" in " ".join(auditar_precio(mutado)), (
        "el auditor aceptó un precio sin el comando que lo mide"
    )


def test_falsador_precio_de_entrada_movido():
    """Subir o bajar la cifra sin volver a medir el sitio es rojo."""
    t = texto()
    bloque = bloque_precio(t)
    mutado = t.replace(bloque, bloque.replace(PRECIO_ENTRADA, "$199/mes"), 1)
    assert "PRECIO_NO_CASA" in " ".join(auditar_precio(mutado)), (
        "el auditor aceptó una cifra de entrada que el bloque ya no publica"
    )


def test_la_clausula_sobrevive_al_salto_de_linea():
    """Regresión: el sujeto sano no puede enrojecer por el ancho del párrafo."""
    t = texto()
    bloque = bloque_precio(t)
    partido = RE_CLAUSULA.sub("is published\non the site", bloque, count=1)
    assert partido != bloque, "el bloque dejó de declarar la cláusula que esta prueba parte"
    assert auditar_precio(t.replace(bloque, partido, 1)) == [], (
        "el auditor mide el ancho de línea del README, no el precio que publica"
    )


def test_falsador_precio_clausula_ausente():
    """El colapso de espaciado no puede volver tautológica la cláusula."""
    t = texto()
    bloque = bloque_precio(t)
    mutado = t.replace(bloque, RE_CLAUSULA.sub("reseñada aquí", bloque, count=1), 1)
    assert mutado != t, "el bloque dejó de declarar la cláusula que este falsador retira"
    assert [x.split(":")[0] for x in auditar_precio(mutado)] == ["PRECIO_SIN_CLAUSULA"], (
        "el auditor aceptó una condición de lanzamiento sin declarar que no está publicada"
    )


def test_falsador_precio_sin_sujeto():
    """Un `curl` cualquiera no es una medición: el bloque tiene que nombrar la fuente."""
    t = texto()
    bloque = bloque_precio(t)
    mutado = t.replace(bloque, bloque.replace(FUENTE_PRECIO, "la página de precios"), 1)
    assert [x.split(":")[0] for x in auditar_precio(mutado)] == ["PRECIO_SIN_SUJETO"], (
        "el auditor aceptó un precio sin la fuente que lo mide"
    )


# ------------------------------------------------- el instrumento, ejercitado
# HUELLA-BADGE-MEDIDO-CON-LECTOR-20261106
ENDPOINT_CORPUS = ("raw.githubusercontent.com/alexisromtz-lab/corpus-medido"
                   "/main/badges/reglas.json")

RE_BADGE = re.compile(
    r"\[!\[(?P<alt>[^\]]*)\]\((?P<url>https://img\.shields\.io/[^)\s]*)\)\]\((?P<href>[^)\s]*)\)")
RE_CIFRA_LITERAL = re.compile(r"(?:^|[-_])(\d+)[-_ ](?:rules?|reglas?)(?:[-_]|$)", re.I)


def badges(t: str) -> list[dict[str, str]]:
    return [m.groupdict() for m in RE_BADGE.finditer(t)]


def auditar_badges(t: str) -> list[str]:
    """Un badge que lleva su cifra escrita a mano es una cifra sin lector.

    El defecto no es que el número sea falso —el `56_rules` era correcto el día
    que se escribió—, es que nada lo habría puesto rojo el día que dejara de
    serlo. Un badge dinámico publica un `url=`: ese endpoint ES el lector.
    """
    salida = []
    for b in badges(t):
        url = b["url"]
        if "/badge/dynamic/" in url:
            if not re.search(r"[?&]url=[^&]+", url):
                salida.append(f"BADGE_DINAMICO_SIN_ENDPOINT: {b['alt']}")
            continue
        mensaje = urllib.parse.unquote(url.split("img.shields.io/badge/", 1)[-1].split("?")[0])
        if RE_CIFRA_LITERAL.search(mensaje):
            salida.append(f"BADGE_CIFRA_SIN_LECTOR: {b['alt']} · {mensaje[:70]}")
    return salida


def test_el_badge_del_corpus_lleva_lector_y_no_cifra():
    marca = [b for b in badges(texto()) if b["alt"] == "corpus-medido"]
    assert len(marca) == 1, "el perfil publica exactamente un badge de corpus-medido"
    endpoint = urllib.parse.unquote(marca[0]["url"])
    assert "dynamic/json" in marca[0]["url"], "el badge debe consultar el medidor, no llevar la cifra"
    assert ENDPOINT_CORPUS in endpoint, f"el endpoint no apunta al medidor: {endpoint}"
    assert "query=$.message" in endpoint, f"el badge no lee el campo medido: {endpoint}"
    assert not RE_CIFRA_LITERAL.search(endpoint), "el badge volvió a escribir la cifra a mano"


def test_ningun_badge_publica_una_cifra_sin_lector():
    assert auditar_badges(texto()) == []


def _mutar_badge(nuevo: str) -> str:
    """Sustituye el badge del corpus por otro: el falsador muta el objeto real."""
    original = texto()
    actual = [b for b in badges(original) if b["alt"] == "corpus-medido"][0]
    linea = f"[![corpus-medido]({actual['url']})]({actual['href']})"
    assert original.count(linea) == 1
    return original.replace(linea, nuevo)


def test_falsador_badge_con_cifra_a_mano():
    mutado = _mutar_badge(
        "[![corpus-medido](https://img.shields.io/badge/corpus--medido-56_rules-111111?style=flat-square)]"
        "(https://github.com/alexisromtz-lab/corpus-medido)")
    hallazgos = auditar_badges(mutado)
    assert len(hallazgos) == 1, hallazgos
    assert hallazgos[0].startswith("BADGE_CIFRA_SIN_LECTOR: corpus-medido · "), hallazgos
    assert "56_rules" in hallazgos[0], hallazgos


def test_falsador_badge_dinamico_sin_endpoint():
    mutado = _mutar_badge(
        "[![corpus-medido](https://img.shields.io/badge/dynamic/json?query=%24.message&label=corpus--medido)]"
        "(https://github.com/alexisromtz-lab/corpus-medido)")
    assert auditar_badges(mutado) == ["BADGE_DINAMICO_SIN_ENDPOINT: corpus-medido"]


def violaciones_badges(t: str) -> list[str]:
    return auditar_badges(t)


def test_los_instrumentos_se_autovalidan():
    """Un instrumento que no pasa su propio banco no mide nada: se ejerce, no se confía."""
    for nombre in ("medir_precio.py", "medir_censo.py"):
        herramienta = RAIZ / "tools" / nombre
        assert herramienta.is_file(), f"INSTRUMENTO_AUSENTE: {herramienta}"
        r = subprocess.run(
            [sys.executable, str(herramienta), "--self-test"],
            cwd=str(RAIZ),
            capture_output=True,
            text=True,
            timeout=180,
        )
        assert r.returncode == 0, f"{nombre} --self-test ⇒ RC {r.returncode}\n{r.stdout}{r.stderr}"


def test_el_instrumento_del_precio_coteja_captura_y_readme():
    """Offline: README ↔ captura firmada. La red la mide `--check`, no el CI."""
    r = subprocess.run(
        [sys.executable, str(RAIZ / "tools" / "medir_precio.py"), "--check-readme"],
        cwd=str(RAIZ),
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert r.returncode == 0, f"RC {r.returncode} · {r.stdout}{r.stderr}"


def test_falsador_captura_del_precio_desfasada(tmp_path):
    """Mover una cifra en la captura sin volver a medir el sitio enrojece el cotejo."""
    datos = json.loads((RAIZ / "precio_medido.json").read_text(encoding="utf-8"))
    datos["escalera"][1]["importe"] = "899"
    falsa = tmp_path / "precio_medido.json"
    falsa.write_text(json.dumps(datos, ensure_ascii=False), encoding="utf-8")
    r = subprocess.run(
        [
            sys.executable,
            str(RAIZ / "tools" / "medir_precio.py"),
            "--check-readme",
            "--captura",
            str(falsa),
            "--readme",
            str(README),
        ],
        cwd=str(RAIZ),
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert r.returncode == 1, f"la captura desfasada no enrojeció: RC {r.returncode}\n{r.stdout}{r.stderr}"


def test_falsador_captura_del_censo_ausente(tmp_path):
    """Un censo que no existe no es un censo vacío: es CENSO_NO_MEDIDO, con su causa."""
    fecha, comando, publicos, error = _leer_censo(tmp_path / "NO_EXISTE.json")
    assert error, "el lector aceptó una captura ausente como censo válido"
    assert not publicos and not fecha and not comando


def test_falsador_captura_del_censo_ilegible(tmp_path):
    rota = tmp_path / "censo_medido.json"
    rota.write_text("{no es json", encoding="utf-8")
    _, _, publicos, error = _leer_censo(rota)
    assert error, "el lector aceptó un JSON ilegible como censo válido"
    assert not publicos
