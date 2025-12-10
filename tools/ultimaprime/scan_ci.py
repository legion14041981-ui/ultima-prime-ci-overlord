#!/usr/bin/env python3
"""
ULTIMA-PRIME: CI diagnosis scanner
Detects blocking errors in CI/pytest logs:
  - NameError: Optional (missing import)
  - ModuleNotFoundError (missing deps)
  - Pydantic regex= usage (v2 migration)
  - pytest markers/fixtures issues

Usage:
  python scan_ci.py --pytest-log path/to/pytest.log
  python scan_ci.py --run-pytest

Output: diagnostics/report.json (machine) + diagnostics/report.txt (human-readable)
"""
import argparse
import json
import re
import subprocess
import pathlib
import sys
from datetime import datetime

ROOT = pathlib.Path(__file__).resolve().parents[2]

def run_pytest_and_capture():
    """Run pytest with detailed output capture."""
    cmd = ["pytest", "-v", "--tb=short", "--capture=no", "--maxfail=3"]
    print(f"[ULTIMA] Запуск: {' '.join(cmd)}")
    p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    return p.returncode, p.stdout

def parse_output(output: str) -> list:
    """Parse pytest output for known error patterns."""
    issues = []
    
    # ❌ Pattern 1: Missing Optional import
    for m in re.finditer(r"NameError: name 'Optional' is not defined.*?\n", output, re.IGNORECASE):
        context_start = max(0, m.start() - 300)
        context = output[context_start:m.end() + 200]
        issues.append({
            "type": "MissingOptionalImport",
            "severity": "HIGH",
            "pattern": "NameError: name 'Optional' is not defined",
            "context": context.strip(),
            "fix": "Добавить 'from typing import Optional' в импорты"
        })
    
    # ❌ Pattern 2: RestrictedPython missing
    for m in re.finditer(r"ModuleNotFoundError: No module named 'RestrictedPython'", output):
        context_start = max(0, m.start() - 300)
        context = output[context_start:m.end() + 200]
        issues.append({
            "type": "MissingDependency",
            "dependency": "RestrictedPython",
            "severity": "HIGH",
            "pattern": "ModuleNotFoundError: No module named 'RestrictedPython'",
            "context": context.strip(),
            "fix": "Добавить 'RestrictedPython>=6.0' в requirements.txt или pyproject.toml"
        })
    
    # ❌ Pattern 3: Pydantic v2 migration (regex → pattern)
    for m in re.finditer(r"Field\([^)]*regex=", output):
        context_start = max(0, m.start() - 300)
        context = output[context_start:m.end() + 200]
        issues.append({
            "type": "PydanticV2Migration",
            "severity": "MEDIUM",
            "pattern": "Field(..., regex=...)",
            "context": context.strip(),
            "fix": "Заменить 'regex=' на 'pattern=' (Pydantic v2)"
        })
    
    # ❌ Pattern 4: Unknown pytest marker
    for m in re.finditer(r"ERROR.*[Uu]nknown pytest\.mark\.(\w+)", output):
        context_start = max(0, m.start() - 200)
        context = output[context_start:m.end() + 200]
        issues.append({
            "type": "UnknownPytestMarker",
            "severity": "MEDIUM",
            "context": context.strip(),
            "fix": "Определить маркер в pytest.ini или conftest.py"
        })
    
    # ❌ Pattern 5: Import errors
    for m in re.finditer(r"ImportError: cannot import name '(\w+)' from '([^']+)'", output):
        name, module = m.groups()
        issues.append({
            "type": "ImportError",
            "severity": "HIGH",
            "imported_name": name,
            "from_module": module,
            "context": output[max(0, m.start() - 200):m.end() + 200].strip(),
            "fix": f"Проверить экспорт '{name}' из модуля '{module}'"
        })
    
    return issues

def main():
    p = argparse.ArgumentParser(
        description="ULTIMA-PRIME CI Scanner — диагностика ошибок CI/pytest"
    )
    p.add_argument(
        "--run-pytest",
        action="store_true",
        help="Запустить pytest локально"
    )
    p.add_argument(
        "--pytest-log",
        type=str,
        default=None,
        help="Путь к сохранённому лог-файлу pytest"
    )
    args = p.parse_args()
    
    # Gather test output
    if args.run_pytest:
        rc, output = run_pytest_and_capture()
    elif args.pytest_log:
        try:
            output = pathlib.Path(args.pytest_log).read_text()
            rc = 0
        except FileNotFoundError:
            print(f"[ERROR] Лог не найден: {args.pytest_log}", file=sys.stderr)
            sys.exit(1)
    else:
        print(
            "[ERROR] Укажите --run-pytest или --pytest-log <path>",
            file=sys.stderr
        )
        sys.exit(2)
    
    # Parse issues
    issues = parse_output(output)
    
    # Create report
    report = {
        "timestamp": datetime.utcnow().isoformat(),
        "return_code": rc,
        "total_issues": len(issues),
        "issues": issues,
        "by_severity": {
            "HIGH": len([i for i in issues if i.get("severity") == "HIGH"]),
            "MEDIUM": len([i for i in issues if i.get("severity") == "MEDIUM"]),
            "LOW": len([i for i in issues if i.get("severity") == "LOW"])
        }
    }
    
    # Save JSON report
    out_dir = ROOT / "diagnostics"
    out_dir.mkdir(exist_ok=True)
    
    json_path = out_dir / "report.json"
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2))
    
    # Save human-readable report
    txt_path = out_dir / "report.txt"
    txt_lines = [
        "═" * 70,
        "ULTIMA-PRIME CI DIAGNOSTIC REPORT",
        f"Время: {report['timestamp']}",
        f"Return code: {rc}",
        "═" * 70,
        f"",
        f"КРИТИЧНЫЕ (HIGH):   {report['by_severity']['HIGH']}",
        f"СРЕДНИЕ (MEDIUM):   {report['by_severity']['MEDIUM']}",
        f"НИЗКИЕ (LOW):       {report['by_severity']['LOW']}",
        f"ВСЕГО:              {report['total_issues']}",
        f"",
        "═" * 70,
    ]
    
    for i, issue in enumerate(issues, 1):
        txt_lines.extend([
            f"",
            f"[{i}] {issue.get('type', 'Unknown')} — {issue.get('severity', 'N/A')}",
            f"    Паттерн: {issue.get('pattern', issue.get('imported_name', 'N/A'))}",
            f"    Решение: {issue.get('fix', 'Manual review needed')}",
            f"    Контекст:",
        ])
        for line in issue.get('context', '').split('\n')[:5]:
            txt_lines.append(f"      {line}")
    
    txt_path.write_text("\n".join(txt_lines))
    
    # Print summary
    print(f"\n✅ [ULTIMA] Диагностика завершена")
    print(f"📊 Найдено проблем: {report['total_issues']}")
    print(f"📁 Отчёт сохранён:")
    print(f"   - JSON:  {json_path}")
    print(f"   - TXT:   {txt_path}")
    print(f"\n💡 Следующий шаг: python tools/ultimaprime/fix_optional_imports.py")
    
    return 0 if len(issues) == 0 else 1

if __name__ == "__main__":
    sys.exit(main())
