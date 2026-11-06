#!/usr/bin/env bash
# instalar.sh — activa el candado de vitrina en ESTE clon.
#
# Por qué existe: el candado vive versionado en `hooks/pre-push`, pero git no
# clona `.git/hooks/` (por seguridad), así que un clon recién hecho no tiene
# candado. Un hook ausente no falla: simplemente no mide, y nadie se entera
# hasta que la vitrina ya está rota. Esto es el acto que convierte un clon en
# un clon vigilado.
#
# Uso:   bash hooks/instalar.sh
# RC:    0 = candado activo · 1 = no se pudo activar (fail-closed, sin verde)
# HUELLA-PERFIL-INSTALADOR-CANDADO-20261106
set -eu

raiz=$(git rev-parse --show-toplevel 2>/dev/null) || {
  echo "FALLO: $(pwd) no está dentro de un repositorio git" >&2; exit 1; }

origen="$raiz/hooks/pre-push"
gitdir=$(git -C "$raiz" rev-parse --absolute-git-dir)

[ -f "$origen" ] || { echo "FALLO: falta el hook versionado $origen" >&2; exit 1; }
[ -x "$origen" ] || chmod +x "$origen"

# El enlace viaja RELATIVO cuando el hook cuelga de `<raiz>/.git`, para que el
# clon se pueda mover de carpeta sin dejar el candado apuntando al vacío. En un
# worktree el git-dir vive fuera del árbol y ahí el enlace se resuelve absoluto.
case "$gitdir" in
  "$raiz/.git") enlace="../../hooks/pre-push" ;;
  *)            enlace="$origen" ;;
esac

mkdir -p "$gitdir/hooks"
ln -sfn "$enlace" "$gitdir/hooks/pre-push"

if [ ! -x "$gitdir/hooks/pre-push" ]; then
  echo "FALLO: el enlace quedó inerte ($gitdir/hooks/pre-push -> $enlace)" >&2
  exit 1
fi

echo "CANDADO ACTIVO: $gitdir/hooks/pre-push -> $enlace"
echo "Mide el README.md del commit que viaja, en cada push y en cada --dry-run."
