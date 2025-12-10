#!/usr/bin/env bash
# ULTIMA-PRIME: Generate draft PR from patches
# Creates local branch + commits, then shows gh pr create command
# NO automatic push or merge

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
PATCH_DIR="$ROOT/tools/ultimaprime/patches"
BR="ultima-ci-fixes-$(date +%s)"
PR_BODY="$ROOT/tools/ultimaprime/PR_BODY.md"

echo ""
echo "════════════════════════════════════"
echo " 🚀 ULTIMA-PRIME: Draft PR Generator"
echo "════════════════════════════════════"
echo ""
echo "⚠️  РЕЖИМ DRY-RUN: Создам ветку и коммиты локально."
echo "   ПУШ И СОЗДАНИЕ PR требуют ТВОЕГО явного подтверждения!"
echo ""

if [ ! -d "$PATCH_DIR" ] || [ -z "$(ls -A "$PATCH_DIR" 2>/dev/null || true)" ]; then
    echo "[ERROR] Папка $PATCH_DIR пуста или не существует."
    echo "         Сначала запусти: python tools/ultimaprime/scan_ci.py --run-pytest"
    exit 1
fi

echo "[1/3] Создаю локальную ветку: $BR"
git checkout -b "$BR" 2>/dev/null || (git fetch origin && git checkout -b "$BR")

echo "[2/3] Применяю патчи из $PATCH_DIR"
patch_count=0
for f in "$PATCH_DIR"/*; do
    [ -f "$f" ] || continue
    
    # Determine target path (reverse name mangling)
    target_rel=$(basename "$f" | sed 's/__/\//g' | sed 's/\.patch$//' | sed 's/\.txt$//')
    target="$ROOT/$target_rel"
    
    # Handle .patch files (full file replacement)
    if [[ "$f" == *.patch ]]; then
        if [ -f "$target" ]; then
            echo "  [PATCH] $target_rel (replace)"
            cp "$f" "$target"
            git add "$target"
            ((patch_count++))
        else
            echo "  [SKIP] $target_rel (не найден)"
        fi
    # Handle .txt files (display as instructions)
    elif [[ "$f" == *.txt ]]; then
        echo "  [INFO] Инструкция в $f"
        cat "$f" | head -3
    fi
done

if [ "$patch_count" -eq 0 ]; then
    echo "[WARN] Не применено ни одного патча. Отменяю ветку."
    git checkout - >/dev/null
    git branch -D "$BR" 2>/dev/null || true
    exit 1
fi

echo "[3/3] Создаю коммит"
git commit -m "chore(ci): apply ULTIMA-PRIME generated fixes (draft)" \
    -m "Diagnostic report: diagnostics/report.json" \
    -m "Generated: $(date -u +%Y-%m-%dT%H:%M:%SZ)"

echo ""
echo "✅ Готово! Применено патчей: $patch_count"
echo ""
echo "[REVIEW] Проверь локально:"
echo "  git show --stat HEAD"
echo "  git diff HEAD~1 HEAD | less"
echo ""
echo "[PUSH & CREATE PR] Если всё в порядке:"
echo ""
echo "  git push origin $BR"
echo ""
echo "  gh pr create \\"
echo "    --title 'chore(ci): ULTIMA-PRIME auto-fixes' \\"
echo "    --body-file tools/ultimaprime/PR_BODY.md \\"
echo "    --base main \\"
echo "    --head $BR \\"
echo "    --draft"
echo ""
echo "  ИЛИ откройи браузер и создай PR вручную."
echo ""
echo "[CANCEL] Если что-то не так:"
echo "  git checkout main && git branch -D $BR"
echo ""
