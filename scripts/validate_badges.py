"""Validate repository-specific README badge claims against checked-in source."""
from pathlib import Path
import re

root = Path(__file__).resolve().parents[1]
readme = (root / "README.md").read_text()
dockerfile = (root / "Dockerfile").read_text()
workflow = root / ".github/workflows/ci.yml"
compose = root / "compose.yml"
code = (root / "watchdog.py").read_text()
license_path = root / "LICENSE"
issues = []

def require(condition, message):
    if not condition:
        issues.append(message)

header = "# Mad Mallard Automation Watchdog\n"
require(readme.startswith(header), "README title changed")
badge_block = readme[len(header):].split("\nStandalone,", 1)[0]
require(badge_block.startswith("\n[!["), "Badges must immediately follow title")
require("Python-3.13" in badge_block and "FROM python:3.13" in dockerfile,
        "Python version badge must match Dockerfile")
require("SQLite" in badge_block and "sqlite3" in code, "SQLite claim not verified")
require("Docker-Compose" in badge_block and compose.exists(), "Compose claim not verified")
require(license_path.exists() and "img.shields.io/github/license/" in badge_block,
        "License badge requires a real LICENSE")
require(workflow.exists() and
        "actions/workflows/ci.yml/badge.svg" in badge_block,
        "Dynamic CI badge must match real workflow")
for stat in ("github/issues/", "github/issues-pr/"):
    require(stat in badge_block, "Missing dynamic statistic: " + stat)
require("badge.svg" in badge_block and "img.shields.io" in badge_block,
        "Use official workflow badge and Shields.io")
# Optional badges are accepted only with their required backing configuration.
if "github/v/release/" in badge_block:
    require("https://github.com/drakeg/madmallard-automation-watchdog/releases" in badge_block,
            "Release badge must link to releases; verify a published release externally")
if "security" in badge_block.lower():
    require(any("security" in f.name.lower() for f in workflow.parent.glob("*.yml")),
            "Security badges require an actual security workflow")
if "vercel" in badge_block.lower():
    require((root / "vercel.json").exists() or (root / ".vercel").exists(),
            "Vercel badge requires verified deployment configuration")
require(len(re.findall(r"\[!\[", badge_block)) >= 7, "Required badges missing")
if issues:
    raise SystemExit("\n".join(issues))
print("README badge claims validated against repository configuration")
