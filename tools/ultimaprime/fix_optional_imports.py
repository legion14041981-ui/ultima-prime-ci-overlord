#!/usr/bin/env python3
"""
Fix missing Optional imports in Python files.
Scans src/ (or specified path) for usage of Optional[] without proper import.
Generates patch files in tools/ultimaprime/patches/

Usage:
  python fix_optional_imports.py [--src-path path/to/src]
"""
import pathlib
import re
import argparse
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]

def find_files_with_optional(src_path: pathlib.Path) -> list:
    """Find all Python files using Optional[]."""
    files = []
    for py_file in src_path.rglob("*.py"):
        try:
            text = py_file.read_text()
            if re.search(r"Optional\s*\[", text):
                files.append(py_file)
        except Exception as e:
            print(f"[WARN] Ошибка при чтении {py_file}: {e}", file=sys.stderr)
    return files

def has_optional_import(text: str) -> bool:
    """Check if Optional is already imported."""
    return bool(
        re.search(r"from\s+typing\s+import\s+.*\bOptional\b", text) or
        re.search(r"from\s+typing\s+import\s*\(", text)  # multiline import
    )

def fix_imports(text: str) -> tuple[str, bool]:
    """Add Optional import if missing. Returns (new_text, was_fixed)."""
    lines = text.split('\n')
    
    # Step 1: Try to add Optional to existing 'from typing import'
    for i, line in enumerate(lines[:50]):
        if re.match(r"\s*from\s+typing\s+import", line):
            # Check if it's a single-line or multi-line import
            if "Optional" not in line:
                # Single-line case
                if line.rstrip().endswith(")"):
                    # Multi-line import — find closing paren
                    import_lines = [i]
                    j = i + 1
                    while j < len(lines) and ")" not in lines[j]:
                        j += 1
                    if j < len(lines) and ")" in lines[j]:
                        # Add Optional before the closing paren
                        lines[j] = lines[j].replace(")", ", Optional)")
                        return '\n'.join(lines), True
                else:
                    # Single-line import
                    lines[i] = line.rstrip() + ", Optional"
                    return '\n'.join(lines), True
    
    # Step 2: Add new import after other imports
    insert_index = 0
    for i, line in enumerate(lines[:50]):
        stripped = line.strip()
        if stripped.startswith("import") or stripped.startswith("from"):
            insert_index = i + 1
        elif stripped == "":
            continue
        elif stripped.startswith("#"):
            continue
        else:
            break
    
    lines.insert(insert_index, "from typing import Optional")
    return '\n'.join(lines), True

def main():
    parser = argparse.ArgumentParser(
        description="ULTIMA-PRIME: Fix missing Optional imports"
    )
    parser.add_argument(
        "--src-path",
        type=str,
        default="src",
        help="Path to source directory (default: src)"
    )
    args = parser.parse_args()
    
    src_path = ROOT / args.src_path
    if not src_path.exists():
        print(f"[WARN] Путь не существует: {src_path}", file=sys.stderr)
        print(f"[INFO] Использую корень репо: {ROOT}")
        src_path = ROOT
    
    # Find files with Optional
    files_with_optional = find_files_with_optional(src_path)
    print(f"[INFO] Найдено файлов с Optional[]: {len(files_with_optional)}")
    
    patch_dir = ROOT / "tools" / "ultimaprime" / "patches"
    patch_dir.mkdir(parents=True, exist_ok=True)
    
    patched_files = []
    for py_file in files_with_optional:
        try:
            original_text = py_file.read_text()
            
            if has_optional_import(original_text):
                print(f"[SKIP] {py_file.relative_to(ROOT)} — Optional уже импортирован")
                continue
            
            # Fix the imports
            new_text, was_fixed = fix_imports(original_text)
            
            if was_fixed:
                # Save as patch file
                rel_path = py_file.relative_to(ROOT).as_posix()
                patch_name = rel_path.replace("/", "__").replace(".py", ".patch")
                patch_file = patch_dir / patch_name
                patch_file.write_text(new_text)
                patched_files.append(rel_path)
                print(f"[PATCH] {rel_path} → {patch_file.name}")
        except Exception as e:
            print(f"[ERROR] {py_file}: {e}", file=sys.stderr)
    
    # Summary
    print(f"\n✅ Создано патчей: {len(patched_files)}")
    if patched_files:
        print(f"📁 Патчи в: {patch_dir}")
        print(f"\n💡 Следующий шаг: python tools/ultimaprime/add_dependency_patch.py")
    
    return 0 if len(patched_files) > 0 else 1

if __name__ == "__main__":
    sys.exit(main())
