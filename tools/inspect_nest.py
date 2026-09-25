#!/usr/bin/env python3
from pathlib import Path
import re

for name in ["about/index.html", "services/emergency-water-removal/index.html", "index.html"]:
    t = Path(name).read_text(encoding="utf-8")
    print("====", name)
    count = 0
    for m in re.finditer(r'<a class="btn[^"]*" href="tel:\+16235550148">', t):
        end = t.find("</a>", m.start())
        if end < 0:
            continue
        inner = t[m.end() : end]
        if "<a " in inner:
            count += 1
            print(re.sub(r"\s+", " ", t[m.start() : end + 4])[:260])
            print("---")
    print("nested count", count)
