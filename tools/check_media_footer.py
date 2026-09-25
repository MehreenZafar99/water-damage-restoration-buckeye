#!/usr/bin/env python3
from pathlib import Path
import re

missing = []
media = []
for p in Path(".").rglob("*.html"):
    if "files" in p.parts:
        continue
    t = p.read_text(encoding="utf-8")
    if "site-footer" in t and "contact@waterdamagerestorationbuckeyeaz.com" not in t:
        missing.append(str(p))
    if 'class="media"' in t or re.search(r"/assets/img/[^\"']+\.webp", t):
        media.append(str(p))
print("footers missing email:", missing)
print("pages still with media/webp refs:", media)
