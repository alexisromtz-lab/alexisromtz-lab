#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Mide el precio que publica la pagina viva y lo coteja con la captura y el README.

HUELLA-TOOL-MEDIR-PRECIO-20261106

SUJETO DECLARADO: una pagina, `https://studiocity.app/`. No "la web", no el
producto entero, no la facturacion. La escalera de planes y la cifra de
lanzamiento que esa pagina imprime hoy.

POR QUE EXISTE. El 2026-11-01 el README publicaba `$299 / $599 / $899` y era
cierto ese dia. El 2026-11-06 la pagina publica `$499 / $799 / $1,199` y el
tercer plan ya no se llama `Premium` sino `Ilimitado`. La cifra estaba tecleada
a mano en una pagina cuya tesis es que nada se teclea a mano, y el unico
instrumento que la vigilaba comparaba el README contra una constante del propio
test: un numero que no puede diferir. Este instrumento mide el objeto.

CONTRATO
  captura  = precio_medido.json (fecha + comando + escalera + lanzamiento)
  --check  coteja la captura contra el sitio vivo  Y  el README contra la captura
  --aplicar firma una captura nueva con la hora UTC del acto (la unica via legitima
           para que una cifra cambie: alguien midio y lo declaro)

RC 0   medicion y cotejo limpios
RC 1   divergencia: nombra la celda (plan, importe, fecha, sujeto o clausula)
RC 2   NO_MEDIDO: red caida, universo vacio o captura ausente — nunca se degrada a 0
RC 20  argumentos incompatibles
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
CAPTURA = RAIZ / "precio_medido.json"
README = RAIZ / "README.md"
SUJETO = "https://studiocity.app/"
COMANDO = "curl -s https://studiocity.app/"

# La pagina renderiza las tarjetas de plan y la tira de estadisticas en el DOM.
# El payload RSC que viaja en el mismo HTML lleva las comillas escapadas (\"),
# asi que estos patrones no lo tocan: miden lo que el visitante ve, una sola vez.
RE_PLAN = re.compile(
    r'text-lg font-bold text-zinc-800">([^<]{1,40})</div>\s*'
    r'<div class="mt-1 text-3xl font-black text-zinc-900">\$([0-9][0-9,.]*)'
)
RE_LANZAMIENTO = re.compile(
    r'text-3xl font-black text-\[var\(--gold-deep\)\]">\$([0-9][0-9,.]*)</p>\s*'
    r'<p class="[^"]*">([^<]{1,80})</p>'
)


# ------------------------------------------------------------------- medicion
def medir(url: str = SUJETO, timeout: int = 25) -> str:
    """El HTML del sujeto. Una caida de red no es un cero: es una excepcion."""
    req = urllib.request.Request(url, headers={"User-Agent": "medir-precio/1"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", "replace")


def extraer(html: str) -> dict:
    """Escalera y lanzamiento tal como los imprime el sujeto. Sin planes = vacio."""
    escalera = [
        {"plan": plan.strip(), "importe": importe, "periodo": "/mes"}
        for plan, importe in RE_PLAN.findall(html)
    ]
    m = RE_LANZAMIENTO.search(html)
    lanzamiento = (
        {"importe": m.group(1), "etiqueta": m.group(2).strip()} if m else None
    )
    return {"escalera": escalera, "lanzamiento": lanzamiento}


def captura_desde(html: str, ahora: datetime | None = None) -> dict:
    ahora = ahora or datetime.now(timezone.utc)
    datos = extraer(html)
    return {
        "sujeto": SUJETO,
        "comando": COMANDO,
        "medido_en": ahora.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "escalera": datos["escalera"],
        "lanzamiento": datos["lanzamiento"],
    }


# -------------------------------------------------------------------- cotejo
def _planes(captura: dict) -> dict[str, str]:
    return {p["plan"]: p["importe"] for p in captura.get("escalera", [])}


def comparar(captura: dict, medido: dict) -> list[str]:
    """Diferencias entre lo firmado y lo que el sitio publica AHORA."""
    a, b = _planes(captura), _planes(medido)
    v: list[str] = []
    for plan, importe in a.items():
        if plan not in b:
            v.append(f"PLAN_FALTANTE: {plan} (${importe}) ya no aparece en el sitio")
        elif b[plan] != importe:
            v.append(f"IMPORTE_MOVIDO: {plan} captura=${importe} sitio=${b[plan]}")
    for plan, importe in b.items():
        if plan not in a:
            v.append(f"PLAN_NUEVO: {plan} (${importe}) está en el sitio y no en la captura")
    la, lb = captura.get("lanzamiento"), medido.get("lanzamiento")
    if la is None and lb is not None:
        v.append(f"LANZAMIENTO_NUEVO: el sitio publica ${lb['importe']} ({lb['etiqueta']})")
    elif la is not None and lb is None:
        v.append(f"LANZAMIENTO_AUSENTE: la captura declara ${la['importe']} y el sitio no lo publica")
    elif la and lb and (la["importe"], la["etiqueta"]) != (lb["importe"], lb["etiqueta"]):
        v.append(
            f"LANZAMIENTO_MOVIDO: captura=${la['importe']} ({la['etiqueta']}) "
            f"sitio=${lb['importe']} ({lb['etiqueta']})"
        )
    return v


def check_readme(texto: str, captura: dict) -> list[str]:
    """Lo que el README publica no puede diferir de la captura firmada."""
    v: list[str] = []
    for p in captura.get("escalera", []):
        celda = f"{p['plan']} ${p['importe']}{p['periodo']}"
        if celda not in texto:
            v.append(f"README_NO_PUBLICA: {celda!r}")
    fecha = captura.get("medido_en", "")[:10]
    if fecha and fecha not in texto:
        v.append(f"README_SIN_FECHA: no publica la fecha de medición {fecha}")
    if captura.get("sujeto") and captura["sujeto"] not in texto:
        v.append(f"README_SIN_SUJETO: no nombra la fuente medida {captura['sujeto']}")
    if captura.get("comando") and "curl" not in texto:
        v.append("README_SIN_COMANDO: no publica el comando que mide la cifra")
    lan = captura.get("lanzamiento")
    if lan and f"${lan['importe']}" not in texto:
        v.append(f"README_NO_PUBLICA_LANZAMIENTO: falta ${lan['importe']} ({lan['etiqueta']})")
    return v


# ------------------------------------------------------------------ self-test
def _fixture(escalera, lanzamiento=True) -> str:
    tarjetas = "".join(
        '<div class="text-lg font-bold text-zinc-800">%s</div>'
        '<div class="mt-1 text-3xl font-black text-zinc-900">$%s'
        '<span class="text-sm font-normal text-zinc-400">/mes</span></div>' % (p, a)
        for p, a in escalera
    )
    tira = (
        '<p class="text-3xl font-black text-[var(--gold-deep)]">$249</p>'
        '<p class="mt-1 text-xs font-semibold uppercase tracking-wider text-zinc-500">'
        "Lanzamiento · primer mes</p>"
        if lanzamiento
        else ""
    )
    return f"<html><body>{tarjetas}{tira}</body></html>"


def self_test() -> int:
    """El banco se mide desde fuera: cada caso declara su veredicto esperado."""
    base = [("Básico", "499"), ("Pro", "799"), ("Ilimitado", "1,199")]
    captura = {
        "sujeto": SUJETO,
        "comando": COMANDO,
        "medido_en": "2026-11-06T00:00:00Z",
        "escalera": [{"plan": p, "importe": a, "periodo": "/mes"} for p, a in base],
        "lanzamiento": {"importe": "249", "etiqueta": "Lanzamiento · primer mes"},
    }
    readme = (
        "2026-11-06 · https://studiocity.app/ · `curl`\n"
        "`Básico $499/mes` · `Pro $799/mes` · `Ilimitado $1,199/mes` · `$249`\n"
    )
    casos = [
        ("objeto sano", comparar(captura, extraer(_fixture(base))), 0),
        ("importe movido",
         comparar(captura, extraer(_fixture([("Básico", "499"), ("Pro", "899"), ("Ilimitado", "1,199")]))),
         1),
        ("plan renombrado",
         comparar(captura, extraer(_fixture([("Básico", "499"), ("Pro", "799"), ("Premium", "1,199")]))),
         2),
        ("lanzamiento retirado",
         comparar(captura, extraer(_fixture(base, lanzamiento=False))),
         1),
        ("readme sano", check_readme(readme, captura), 0),
        ("readme con otra cifra", check_readme(readme.replace("$799", "$899"), captura), 1),
        ("readme sin comando", check_readme(readme.replace("`curl`", "la página"), captura), 1),
    ]

    fallos = 0
    for nombre, violaciones, esperado in casos:
        if len(violaciones) != esperado:
            fallos += 1
            print(f"FALLA · {nombre}: esperado {esperado} violaciones, medido "
                  f"{len(violaciones)} → {violaciones}", file=sys.stderr)
    if extraer("<html>sin planes</html>")["escalera"]:
        fallos += 1
        print("FALLA · universo vacio: el extractor inventó planes donde no hay", file=sys.stderr)
    total = len(casos) + 1
    if fallos:
        print(f"SELF-TEST FALLIDO · {fallos} de {total} controles", file=sys.stderr)
        return 1
    print(f"SELF-TEST OK · {total}/{total} controles")
    return 0


# ---------------------------------------------------------------------- main
def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Mide el precio publicado y lo coteja.")
    p.add_argument("--captura", type=Path, default=CAPTURA)
    p.add_argument("--readme", type=Path, default=README)
    p.add_argument("--html", type=Path, default=None,
                   help="mide sobre un HTML guardado en vez de la red (reproducibilidad)")
    p.add_argument("--check", action="store_true", help="captura↔sitio y README↔captura")
    p.add_argument("--check-readme", action="store_true", help="solo README↔captura")
    p.add_argument("--aplicar", action="store_true", help="firma una captura nueva")
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
            print(f"RC 1 · {len(violaciones)} celdas del README no casan con la captura", file=sys.stderr)
            return 1
        print("RC 0 · README = captura")
        return 0

    try:
        html = args.html.read_text(encoding="utf-8") if args.html else medir()
    except (urllib.error.URLError, OSError) as e:
        print(f"RC 2 · NO_MEDIDO: {e}", file=sys.stderr)
        return 2

    medido = captura_desde(html)
    if not medido["escalera"]:
        print("RC 2 · NO_MEDIDO: el sujeto no publica ninguna tarjeta de plan", file=sys.stderr)
        return 2

    if args.aplicar:
        args.captura.write_text(json.dumps(medido, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"CAPTURA FIRMADA · {args.captura} · {medido['medido_en']}")
        for p_ in medido["escalera"]:
            print(f"  {p_['plan']} ${p_['importe']}{p_['periodo']}")
        if medido["lanzamiento"]:
            print(f"  lanzamiento ${medido['lanzamiento']['importe']} ({medido['lanzamiento']['etiqueta']})")
        return 0

    violaciones = comparar(captura, medido)
    violaciones += check_readme(args.readme.read_text(encoding="utf-8"), captura)
    for x in violaciones:
        print(x)
    if violaciones:
        print(f"RC 1 · {len(violaciones)} divergencias entre captura, sitio y README", file=sys.stderr)
        return 1
    print("RC 0 · captura = sitio = README")
    return 0


if __name__ == "__main__":
    sys.exit(main())
