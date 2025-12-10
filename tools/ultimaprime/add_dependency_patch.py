#!/usr/bin/env python3
"""
Generate patch instructions for adding missing dependencies.
Checks for RestrictedPython and other common deps.

Usage:
  python add_dependency_patch.py [--dependencies RestrictedPython,pydantic]
"""
import pathlib
import sys
import argparse
import json

ROOT = pathlib.Path(__file__).resolve().parents[2]

def main():
    parser = argparse.ArgumentParser(
        description="ULTIMA-PRIME: Add missing dependencies patch"
    )
    parser.add_argument(
        "--dependencies",
        type=str,
        default="RestrictedPython,pydantic",
        help="Comma-separated list of dependencies to check/add"
    )
    args = parser.parse_args()
    
    deps_to_check = [d.strip() for d in args.dependencies.split(",")]
    patch_dir = ROOT / "tools" / "ultimaprime" / "patches"
    patch_dir.mkdir(parents=True, exist_ok=True)
    
    req_file = ROOT / "requirements.txt"
    pyproject_file = ROOT / "pyproject.toml"
    
    patches_created = []
    
    for dep in deps_to_check:
        # Check requirements.txt
        if req_file.exists():
            content = req_file.read_text()
            if dep not in content:
                patch_content = f"""PATCH for requirements.txt:
Add the following line:

{dep}>=6.0

Run:
  echo \"{dep}>=6.0\" >> requirements.txt
"""
                patch_file = patch_dir / f"add_{dep.lower()}_to_requirements.txt"
                patch_file.write_text(patch_content)
                patches_created.append(("requirements.txt", dep, patch_file))
                print(f"[PATCH] requirements.txt: добавить {dep}")
        
        # Check pyproject.toml
        if pyproject_file.exists():
            content = pyproject_file.read_text()
            if dep not in content:
                patch_content = f"""PATCH for pyproject.toml:
Add to [project] dependencies section:

  \"{dep}>=6.0",

Or if using poetry:
  poetry add {dep}>=6.0
"""
                patch_file = patch_dir / f"add_{dep.lower()}_to_pyproject.txt"
                patch_file.write_text(patch_content)
                patches_created.append(("pyproject.toml", dep, patch_file))
                print(f"[PATCH] pyproject.toml: добавить {dep}")
    
    # Create summary
    if patches_created:
        summary = {
            "total_patches": len(patches_created),
            "patches": [
                {"file": f[0], "dependency": f[1], "patch_file": str(f[2].relative_to(ROOT))}
                for f in patches_created
            ]
        }
        summary_file = patch_dir / "DEPENDENCIES_PATCH_SUMMARY.json"
        summary_file.write_text(
            json.dumps(summary, ensure_ascii=False, indent=2)
        )
        print(f"\n✅ Создано патчей зависимостей: {len(patches_created)}")
        print(f"📁 Сводка в: {summary_file}")
        print(f"\n💡 Следующий шаг: bash tools/ultimaprime/generate_pr_patch.sh")
    else:
        print(f"[INFO] Все зависимости уже присутствуют.")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
