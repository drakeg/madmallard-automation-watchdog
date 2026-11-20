"""Compatibility entry point for consolidated badge validation."""
from pathlib import Path
import subprocess
import sys
subprocess.run([sys.executable, str(Path(__file__).with_name('readme_badges.py')), '--check'], check=True)
