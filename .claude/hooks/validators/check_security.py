#!/usr/bin/env python3
"""Escaneo básico de seguridad en archivos staged."""

import re
import subprocess
import sys

# Patrones peligrosos comunes (OWASP-inspired)
DANGEROUS_PATTERNS = [
    (r'eval\s*\(', "eval() — riesgo de inyección de código"),
    (r'exec\s*\(', "exec() — riesgo de inyección de código"),
    (r'__import__\s*\(', "__import__() — import dinámico sospechoso"),
    (r'subprocess\..*shell\s*=\s*True', "subprocess con shell=True — riesgo de inyección"),
    (r'os\.system\s*\(', "os.system() — usar subprocess en su lugar"),
    (r'pickle\.loads?\s*\(', "pickle.load() — deserialización insegura"),
    (r'yaml\.load\s*\([^)]*\)\s*$', "yaml.load() sin Loader — usar safe_load"),
    (r'SELECT.*\+.*\bfrom\b', "Posible SQL injection por concatenación"),
    (r'f["\'].*SELECT.*FROM', "Posible SQL injection en f-string"),
    (r'\.format\(.*\).*SELECT', "Posible SQL injection en .format()"),
    (r'dangerouslySetInnerHTML', "dangerouslySetInnerHTML — riesgo XSS"),
    (r'innerHTML\s*=', "innerHTML — riesgo XSS"),
]

EXCLUDED_FILES = {"check_security.py", "check_prompts.py", "CLAUDE.md"}
EXCLUDED_DIRS = {".claude/hooks/"}


def main() -> int:
    result = subprocess.run(
        ["git", "diff", "--cached", "--name-only", "--diff-filter=ACMR"],
        capture_output=True, text=True,
    )
    staged_files = [f for f in result.stdout.strip().split("\n") if f]

    issues: list[str] = []
    for filepath in staged_files:
        basename = filepath.split("/")[-1]
        if basename in EXCLUDED_FILES:
            continue
        if any(filepath.startswith(d) or f"/{d}" in filepath for d in EXCLUDED_DIRS):
            continue
        if not filepath.endswith((".py", ".ts", ".tsx", ".js", ".jsx")):
            continue

        try:
            diff_result = subprocess.run(
                ["git", "diff", "--cached", "--", filepath],
                capture_output=True, text=True,
            )
            added_lines = [
                (i, line[1:])
                for i, line in enumerate(diff_result.stdout.split("\n"), 1)
                if line.startswith("+") and not line.startswith("+++")
            ]
        except Exception:
            continue

        for line_num, line in added_lines:
            for pattern, description in DANGEROUS_PATTERNS:
                if re.search(pattern, line, re.IGNORECASE):
                    issues.append(f"  ⚠ {filepath} — {description}")
                    break  # Solo reportar una vez por línea

    if issues:
        # Deduplicate
        unique_issues = list(dict.fromkeys(issues))
        print("❌ Posibles vulnerabilidades de seguridad en código nuevo:")
        print("\n".join(unique_issues))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
