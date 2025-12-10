#!/usr/bin/env bash
# ULTIMA-PRIME: Apply patches with confirmation prompts
# Safe, interactive patch application

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
PATCH_DIR="$ROOT/tools/ultimaprime/patches"

echo ""
echo "════════════════════════════════════"
echo " 💪 ULTIMA-PRIME: Interactive Patch Applicator"
echo "════════════════════════════════════"
echo ""

if [ ! -d "$PATCH_DIR" ]; then
    echo "[ERROR] Патч-директория не найдена: $PATCH_DIR"
    exit 1
fi

patches=("$PATCH_DIR"/*.patch 2>/dev/null || true)
if [ ${#patches[@]} -eq 0 ] || [ -z "${patches[0]}" ]; then
    echo "[INFO] Нет .patch файлов в $PATCH_DIR"
    exit 0
fi

echo "Найдено патчей: ${#patches[@]}"
echo ""

applied=0
skipped=0

for patch_file in "${patches[@]}"; do
    [ -f "$patch_file" ] || continue
    
    patch_name=$(basename "$patch_file")
    target_rel=$(echo "$patch_name" | sed 's/__/\//g' | sed 's/\.patch$//')
    target="$ROOT/$target_rel"
    
    echo "────────────────────────────"
    echo "[PATCH] $target_rel"
    echo "────────────────────────────"
    
    if [ ! -f "$target" ]; then
        echo "[SKIP] Целевой файл не найден: $target"
        ((skipped++))
        continue
    fi
    
    # Show diff (first 20 lines)
    echo ""
    echo "[DIFF] Первые изменения:"
    diff -u "$target" "$patch_file" 2>/dev/null | head -20 || echo "  (не удалось показать diff)"
    echo ""
    
    # Prompt for confirmation
    read -p "Применить этот патч? [y/N] " -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        cp "$patch_file" "$target"
        echo "✅ Применён: $target_rel"
        ((applied++))
    else
        echo "⏸ Пропущен: $target_rel"
        ((skipped++))
    fi
    echo ""
done

echo "════════════════════════════════════"
echo "Итоги: Применено=$applied, Пропущено=$skipped"
echo "════════════════════════════════════"
echo ""

if [ "$applied" -gt 0 ]; then
    echo "Следующие шаги:"
    echo "  1. git status"
    echo "  2. git add <files>"
    echo "  3. git commit -m \"chore: apply patches\""
fi
