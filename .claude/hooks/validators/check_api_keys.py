#!/usr/bin/env python3
"""Escanea archivos staged en git buscando API keys hardcodeadas."""

import re
import subprocess
import sys

PATTERNS = [
    (r'AIza[0-9A-Za-z_-]{35}', "Google API Key"),
    (r'lsv2_[a-zA-Z0-9]{20,}', "LangSmith API Key"),
    (r'sk-[a-zA-Z0-9]{20,}', "Secret Key genérica (sk-*)"),
    (r'ghp_[a-zA-Z0-9]{36}', "GitHub Personal Access Token"),
    (r'ghu_[a-zA-Z0-9]{36}', "GitHub User Token"),
    (r'AKIA[0-9A-Z]{16}', "AWS Access Key ID"),
]

EXCLUDED_FILES = {".env", ".env.example", ".env.local", ".gitignore", "CLAUDE.md"}
EXCLUDED_EXTENSIONS = {".db", ".sqlite", ".png", ".jpg", ".jpeg", ".webp", ".ico"}


def main() -> int:
    result = subprocess.run(
        ["git", "diff", "--cached", "--name-only", "--diff-filter=ACMR"],
        capture_output=True, text=True,
    )
    staged_files = [f for f in result.stdout.strip().split("\n") if f]

    errors: list[str] = []
    for filepath in staged_files:
        basename = filepath.split("/")[-1]
        ext = "." + basename.rsplit(".", 1)[-1] if "." in basename else ""

        if basename in EXCLUDED_FILES or ext in EXCLUDED_EXTENSIONS:
            continue

        try:
            diff_result = subprocess.run(
                ["git", "diff", "--cached", "--", filepath],
                capture_output=True, text=True,
            )
            added_lines = [
                line[1:] for line in diff_result.stdout.split("\n")
                if line.startswith("+") and not line.startswith("+++")
            ]
            content = "\n".join(added_lines)
        except Exception:
            continue

        for pattern, name in PATTERNS:
            matches = re.findall(pattern, content)
            if matches:
                errors.append(f"  ⚠ {filepath}: posible {name} hardcodeada ({matches[0][:12]}...)")

    if errors:
        print("❌ API keys hardcodeadas detectadas:")
        print("\n".join(errors))
        print("\nUsa variables de entorno (.env) en lugar de hardcodear claves.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
