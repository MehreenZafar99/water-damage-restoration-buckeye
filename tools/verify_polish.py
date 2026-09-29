#!/usr/bin/env python3
from pathlib import Path
import re

idx = Path("index.html").read_text(encoding="utf-8")
print("email", "contact@waterdamagerestorationbuckeyeaz.com" in idx)
print("address", "Yuma Rd" in idx)
print("process-flow", "process-flow" in idx)
print("content-bound", idx.count("content-bound"))

body = re.split(r"</head>", idx, 1)[1]
body = re.sub(r"<script.*?</script>", "", body, flags=re.S)
tmp = re.sub(r'<a class="btn[^"]*"[^>]*>.*?</a>', "", body, flags=re.S)
print("plain phones left", re.findall(r"\(623\) 555-0148", tmp))

m = re.search(r'class="emergency-bar".{0,350}', idx, re.S)
print("emergency:", re.sub(r"\s+", " ", m.group(0)[:280]) if m else "none")

svc = Path("services/emergency-water-removal/index.html").read_text(encoding="utf-8")
print("svc email/addr", "contact@" in svc, "Yuma Rd" in svc)
print("nested btn", bool(re.search(r'btn--call[^>]*>[\s\S]{0,180}<a class="btn', svc)))

# count pages missing email
missing = []
for p in Path(".").rglob("*.html"):
    if "files" in p.parts:
        continue
    t = p.read_text(encoding="utf-8")
    if "site-footer" in t and "contact@waterdamagerestorationbuckeyeaz.com" not in t:
        missing.append(str(p))
print("footers missing email", missing[:10], "count", len(missing))
