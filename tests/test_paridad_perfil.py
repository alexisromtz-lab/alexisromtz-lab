#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Aparato semántico de Nivel 6 para el repositorio de perfil.

Este repositorio no tiene motor numérico: su único objeto medible es la PROMESA
que el README le hace al lector. El aparato sustituye «los ficheros existen y
compilan» (`.github/verify_manifest.py`, retirado) por paridad verificable entre
lo que el README **declara** y lo que el README **contiene**:

  1. Cuerpo y huellas — el README existe, pasa de 50 líneas y lleva sus marcas.
  2. Cifra declarada = filas medidas, en los DOS inventarios:
       · «## Start here — six repositories» declara SEIS y su tabla tiene 6 filas;
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

CENSO: de dónde sale y por qué está pineado. Medido el 2026-10-22 con
`gh repo list alexisromtz-lab --limit 200 --json name,visibility` filtrando
`visibility == "PUBLIC"` (19 repos). El mismo día el núcleo del laboratorio pasó a privado y se
publicó `auditoria-ci`: el censo se vuelve a medir, no se ensancha a ojo. El CI de este aparato no consulta la API:
el censo es un DATO FECHADO y se declara como tal. El invariante es de dirección
única, `citado ⊆ censo`: un repositorio público NUEVO no rompe el perfil; un
enlace a uno inexistente sí. Cuando el namespace cambie, se vuelve a medir y se
mueve la fecha — no se ensancha el censo a ojo para que el test pase.

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

import re
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
README = RAIZ / "README.md"

CENSO_MEDIDO = "2026-10-22"
CENSO_COMANDO = (
    "gh repo list alexisromtz-lab --limit 200 --json name,visibility "
    "--jq '[.[] | select(.visibility==\"PUBLIC\") | .name]'"
)
CENSO_PUBLICO = frozenset(
    {
        "acustica-monotile",
        "alexisromtz-lab",
        "ast-channel-router",
        "auditor-toolkit",
        "auditoria-ci",
        "ci-fail-closed-falsifier",
        "fotonica-monotile",
        "git-preflight-gate",
        "gw-rw-zerilli",
        "optica-kerr-2d",
        "plasma-ade",
        "platino-corpus",
        "protocol-core",
        "protocol-core-dist",
        "qnm",
        "red-green-sandbox",
        "rf-signal-integrity",
        "sfqed-paper",
        "vllm-omni",
    }
)

SECCION_INICIO = "## Start here"
SECCION_ORIGEN = "## Origin"
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
    assert not violaciones("REPO_HUERFANO", t), violaciones("REPO_HUERFANO", t)
    assert CENSO_COMANDO.strip(), "el censo tiene que declarar cómo se midió"
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
