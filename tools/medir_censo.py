#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Mide el censo de repositorios publicos de la cuenta y lo coteja con la captura.

HUELLA-TOOL-MEDIR-CENSO-20261106

SUJETO DECLARADO: los repositorios con visibilidad `PUBLIC` de la cuenta
`alexisromtz-lab`, tal como los lista la API de GitHub en el instante del acto.
No "mi trabajo", no "mis proyectos": repositorios publicos clonables.

POR QUE EXISTE. El censo estaba congelado en una constante del test
(`CENSO_MEDIDO = "2026-10-30"`, 22 nombres dentro de un `frozenset`) y el README
publicaba un repo —`corpus-medido`— que llego a publico DESPUES de esa foto.
Resultado: el README decia la verdad y el instrumento lo llamaba huerfano; el CI
del perfil llevaba rojo desde 2026-11-04T17:28 por un numero que no puede
diferir. Un censo medido es una sonda con fecha, no una lista tecleada.

CONTRATO
  captura  = censo_medido.json (fecha + comando + nombres publicos ordenados)
  --check  coteja la captura contra `gh`  Y  el README contra la captura
  --aplicar firma un censo nuevo con la hora UTC del acto

RC 0   medicion y cotejo limpios
RC 1   divergencia: nombra los repositorios añadidos (+) y retirados (−)
RC 2   NO_MEDIDO: `gh` ausente o sin sesion, universo vacio o captura ausente
RC 20  argumentos incompatibles
"""

from __future__ import annotations

import argparse
import json
import subprocess  # noqa: S404 - gh es el sujeto, no un fin
import sys
from datetime import datetime, timezone
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
CAPTURA = RAIZ / "censo_medido.json"
README = RAIZ / "README.md"
CUENTA = "alexisromtz-lab"
COMANDO = f"gh repo list {CUENTA} --limit 200 --json name,visibility"


def medir(cuenta: str = CUENTA, timeout: int = 60) -> list[str]:
    """Nombres con visibilidad PUBLIC. Un fallo de `gh` es NO_MEDIDO, no un cero."""
    proc = subprocess.run(  # noqa: S603
        ["gh", "repo", "list", cuenta, "--limit", "200", "--json", "name,visibility"],
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"gh RC {proc.returncode}: {proc.stderr.strip()[:200]}")
    datos = json.loads(proc.stdout or "[]")
    return sorted(r["name"] for r in datos if r.get("visibility") == "PUBLIC")


def captura_desde(nombres: list[str], ahora: datetime | None = None) -> dict:
    ahora = ahora or datetime.now(timezone.utc)
    return {
        "cuenta": CUENTA,
        "comando": COMANDO,
        "medido_en": ahora.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "publicos": sorted(nombres),
    }


def comparar(captura: dict, medido: list[str]) -> list[str]:
    """Altas y bajas entre lo firmado y lo que la cuenta publica AHORA."""
    a, b = set(captura.get("publicos", [])), set(medido)
    v = [f"REPO_NUEVO: {n} es público y no está en la captura" for n in sorted(b - a)]
    v += [f"REPO_RETIRADO: {n} estaba en la captura y ya no es público" for n in sorted(a - b)]
    return v


def check_readme(texto: str, captura: dict) -> list[str]:
    """Todo repo que el README enlaza tiene que existir en el censo firmado.

    Una sola direccion. El perfil enlaza una seleccion, no los publicos enteros:
    exigir que nombre los N publicos inventaria una obligacion que el documento
    no tiene. La direccion obligatoria es la otra: un enlace a un repo que no
    existe es una promesa rota, y era el defecto medido.
    """
    publicos = set(captura.get("publicos", []))
    return [
        f"README_ENCUENTRA_HUERFANO: {n} no existe en el censo medido"
        for n in sorted(_enlazados(texto) - publicos)
    ]


def _enlazados(texto: str) -> set[str]:
    """Repos propios que el README enlaza: `github.com/<cuenta>/<repo>`."""
    out: set[str] = set()
    marca = f"github.com/{CUENTA}/"
    i = texto.find(marca)
    while i != -1:
        j = i + len(marca)
        nombre = ""
        while j < len(texto) and (texto[j].isalnum() or texto[j] in "-_."):
            nombre += texto[j]
            j += 1
        if nombre and not nombre.endswith(".git"):
            out.add(nombre)
        i = texto.find(marca, j)
    return out


# ------------------------------------------------------------------ self-test
def self_test() -> int:
    base = ["corpus-medido", "git-preflight-gate", "la-auditora"]
    captura = {
        "cuenta": CUENTA,
        "comando": COMANDO,
        "medido_en": "2026-11-06T00:00:00Z",
        "publicos": base,
    }
    readme = " · ".join(f"https://github.com/{CUENTA}/{n}" for n in base)
    casos = [
        ("censo sano", comparar(captura, base), 0),
        ("alta", comparar(captura, base + ["nuevo"]), 1),
        ("baja", comparar(captura, base[:-1]), 1),
        ("readme sano", check_readme(readme, captura), 0),
        ("readme que cambia un repo por otro",
         check_readme(readme.replace(base[0], "otro"), captura), 1),
        ("readme huerfano",
         check_readme(readme + f" https://github.com/{CUENTA}/fantasma", captura), 1),
    ]

    fallos = 0
    for nombre, violaciones, esperado in casos:
        if len(violaciones) != esperado:
            fallos += 1
            print(f"FALLA · {nombre}: esperado {esperado} violaciones, medido "
                  f"{len(violaciones)} → {violaciones}", file=sys.stderr)
    lexer = _enlazados(
        f"x https://github.com/{CUENTA}/git-preflight-gate/blob/main/README.md y"
    )
    if lexer != {"git-preflight-gate"}:
        fallos += 1
        print(f"FALLA · el lexer de enlaces midió {lexer} sobre una ruta de archivo",
              file=sys.stderr)
    total = len(casos) + 1
    if fallos:
        print(f"SELF-TEST FALLIDO · {fallos} de {total} controles", file=sys.stderr)
        return 1
    print(f"SELF-TEST OK · {total}/{total} controles")
    return 0


# ---------------------------------------------------------------------- main
def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Mide el censo de repos públicos y lo coteja.")
    p.add_argument("--captura", type=Path, default=CAPTURA)
    p.add_argument("--readme", type=Path, default=README)
    p.add_argument("--check", action="store_true", help="captura↔cuenta y README↔captura")
    p.add_argument("--check-readme", action="store_true", help="solo README↔captura")
    p.add_argument("--aplicar", action="store_true", help="firma un censo nuevo")
    p.add_argument("--self-test", action="store_true")
    args = p.parse_args(argv)

    if args.self_test:
        return self_test()
    if args.aplicar and (args.check or args.check_readme):
        print("RC 20 · --aplicar no se combina con --check/--check-readme", file=sys.stderr)
        return 20
    if not (args.aplicar or args.check or args.check_readme):
        print("RC 20 · declara --check, --check-readme o --aplicar", file=sys.stderr)
        return 20

    if not args.captura.is_file() and not args.aplicar:
        print(f"RC 2 · NO_MEDIDO: la captura {args.captura} no existe", file=sys.stderr)
        return 2

    captura = json.loads(args.captura.read_text(encoding="utf-8")) if args.captura.is_file() else None

    if args.check_readme:
        violaciones = check_readme(args.readme.read_text(encoding="utf-8"), captura)
        for x in violaciones:
            print(x)
        if violaciones:
            print(f"RC 1 · {len(violaciones)} celdas del README no casan con el censo", file=sys.stderr)
            return 1
        print("RC 0 · README = censo")
        return 0

    try:
        nombres = medir()
    except (RuntimeError, OSError, subprocess.SubprocessError, json.JSONDecodeError) as e:
        print(f"RC 2 · NO_MEDIDO: {e}", file=sys.stderr)
        return 2
    if not nombres:
        print("RC 2 · NO_MEDIDO: la cuenta no publica ningún repositorio", file=sys.stderr)
        return 2

    if args.aplicar:
        args.captura.write_text(
            json.dumps(captura_desde(nombres), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        print(f"CENSO FIRMADO · {args.captura} · {len(nombres)} repos públicos")
        return 0

    violaciones = comparar(captura, nombres)
    violaciones += check_readme(args.readme.read_text(encoding="utf-8"), captura)
    for x in violaciones:
        print(x)
    if violaciones:
        print(f"RC 1 · {len(violaciones)} divergencias entre captura, cuenta y README", file=sys.stderr)
        return 1
    print(f"RC 0 · captura = cuenta = README ({len(nombres)} repos)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
