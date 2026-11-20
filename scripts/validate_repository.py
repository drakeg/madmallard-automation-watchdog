"""Validate selected central requirements without fetching remote code."""
from pathlib import Path
import subprocess
import sys

root = Path(__file__).resolve().parents[1]
required = ('README.md', 'AGENTS.md', 'CONTRIBUTING.md', 'SPRINTS.md',
            'BACKLOG.md', 'RELEASES.md', 'SECURITY.md', 'STANDARDS.md', 'PILOT.md')
missing = [name for name in required if not (root / name).is_file() or not (root / name).read_text().strip()]
if missing:
    raise SystemExit('Missing/empty required documentation: ' + ', '.join(missing))
subprocess.run([sys.executable, str(root / 'scripts/readme_badges.py'), '--check'], check=True)
print('Repository documentation and badges validated')
