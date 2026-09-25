#!/usr/bin/env python3
"""Remove placeholder media figures from all pages."""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
FIG = re.compile(r"<figure\s+class=\"media\"[^>]*>.*?</figure>\s*", re.I | re.S)

n = 0
for p in ROOT.rglob("*.html"):
    if "files" in p.parts or "content" in p.parts:
        continue
    t = p.read_text(encoding="utf-8")
    nt = FIG.sub("", t)
    if nt != t:
        p.write_text(nt, encoding="utf-8", newline="\n")
        n += 1
print(f"Removed media figures from {n} files")
