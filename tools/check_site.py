#!/usr/bin/env python3
"""
Site checker for waterdamagerestorationbuckeyeaz.com
Run from the project root:  python3 tools/check_site.py
Optional: only check some pages:  python3 tools/check_site.py 03 04 05
Prints PASS or a list of problems for every page. Fix every problem, then run again.
"""
import re, sys, json, html, glob, os
from html.parser import HTMLParser

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOMAIN = "https://waterdamagerestorationbuckeyeaz.com"
PHONE_OK = {"(623) 555-0148", "tel:+16235550148", "+1-623-555-0148"}
FORBIDDEN_PLACES = ["phoenix", "goodyear", "avondale", "litchfield", "tonopah", "surprise, az",
                    "glendale", "peoria", "tolleson", "waddell", "west valley", "scottsdale", "mesa", "tempe"]
FORBIDDEN_TEXT = ["lorem ipsum", "todo", "coming soon", "placeholder", "developer note", "rank and rent", "lead gen"]
ALLOWED_HEX = {"#5b1e2d","#3f1420","#8c6a75","#ece8e6","#ffffff","#fff","#2a2326","#6b5f63","#ddd5d2","#f2a900",
               "#d99700","#2a1e00","#b42318","#fbeae8","#f6efef","#d5c4c8","#5e2a38","#c9a9b3","#2b0e16","#8c5e6b",
               "#c9bfbc","#000","#000000"}

class Text(HTMLParser):
    def __init__(self):
        super().__init__(); self.out=[]; self.skip=0
    def handle_starttag(self, t, a):
        if t in ("script","style"): self.skip+=1
    def handle_endtag(self, t):
        if t in ("script","style"): self.skip-=1
    def handle_data(self, d):
        if not self.skip: self.out.append(d)

def norm(s):
    s = html.unescape(s)
    s = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", s)      # md links -> text
    s = re.sub(r"[*_`#>]", "", s)
    s = s.replace("\u2019","'").replace("\u2018","'").replace("\u201c",'"').replace("\u201d",'"')
    return re.sub(r"\s+", " ", s).strip().lower()

def md_files():
    return sorted(glob.glob(os.path.join(ROOT, "content", "batch-*", "*.md")))

def parse_md(path):
    t = open(path, encoding="utf-8").read()
    head = {k: (re.search(r"\*\*"+k+r":\*\*\s*(.+)", t) or [None,None])[1] for k in ["URL","Title tag","Meta description","H1"]}
    body = t.split("\n---\n",1)[1] if "\n---\n" in t else t
    sentences = []
    for line in body.splitlines():
        line=line.strip()
        if not line or line.startswith("*(Developer note") or line.startswith("**Hero") or line.startswith("**Buttons") or line=="---" or " · " in line: continue
        line = re.sub(r"^(\d+\.|-|#+)\s*", "", line)
        line = re.sub(r"^\*\*Intro:\*\*\s*", "", line)
        line = re.sub(r"\*\*(.+?)\*\*", lambda m: m.group(1).rstrip(".:") + "\n", line)
        for s in re.split(r"(?<=[.?!])\s+|\n", line):
            s = norm(s)
            if len(s) > 25: sentences.append(s)
    return head, sentences

def page_path(url):
    return os.path.join(ROOT, url.strip("/"), "index.html") if url.strip("/") else os.path.join(ROOT, "index.html")

def check_page(md):
    head, sentences = parse_md(md)
    url = head["URL"].strip()
    p = page_path(url); probs = []
    if not os.path.exists(p): return url, ["page file missing: " + os.path.relpath(p, ROOT)]
    doc = open(p, encoding="utf-8").read(); low = doc.lower()

    title = re.search(r"<title>(.*?)</title>", doc, re.S)
    if not title or norm(title.group(1)) != norm(head["Title tag"]): probs.append("title tag does not match the .md file")
    desc = re.search(r'<meta name="description" content="(.*?)"', doc)
    if not desc or norm(desc.group(1)) != norm(head["Meta description"]): probs.append("meta description does not match")
    h1s = re.findall(r"<h1[^>]*>(.*?)</h1>", doc, re.S)
    if len(h1s) != 1: probs.append(f"found {len(h1s)} h1 tags, need exactly 1")
    elif norm(re.sub("<[^>]+>","",h1s[0])) != norm(head["H1"]): probs.append("h1 does not match")
    can = re.search(r'<link rel="canonical" href="(.*?)"', doc)
    if not can or can.group(1) != DOMAIN + url: probs.append("canonical missing or wrong")

    for s in re.findall(r'<script type="application/ld\+json">(.*?)</script>', doc, re.S):
        try: json.loads(s)
        except Exception: probs.append("invalid JSON-LD block")
    faqs = len(re.findall(r"<details", doc))
    if faqs and '"FAQPage"' not in doc: probs.append("page has FAQs but no FAQPage schema")

    tp = Text(); tp.feed(doc); text = norm(" ".join(tp.out))
    missing = [s for s in sentences if s not in text]
    if missing:
        probs.append(f"{len(missing)} sentences from the .md file are missing or changed, first ones:")
        probs += ["   > " + m[:110] for m in missing[:5]]

    for place in FORBIDDEN_PLACES:
        if re.search(r"\b" + re.escape(place) + r"\b", text) or re.search(r"\b" + re.escape(place) + r"\b", low): probs.append(f"mentions outside place: {place}")
    for bad in FORBIDDEN_TEXT:
        if re.search(r"\b" + re.escape(bad) + r"\b", text): probs.append(f"visible text contains: {bad}")
    if "\u2014" in text: probs.append("em dash found in visible text")
    for num in set(re.findall(r"\(?\+?1?[\s\-]?\(?\d{3}\)?[\s\-.]?\d{3}[\s\-.]\d{4}", doc)):
        n = num.strip()
        if n not in PHONE_OK and not any(n in ok for ok in PHONE_OK): probs.append(f"odd phone format: {n}")
    return url, probs

def check_links():
    probs=[]
    for f in glob.glob(os.path.join(ROOT, "**", "*.html"), recursive=True):
        if "/_templates/" in f or "/content/" in f: continue
        for href in re.findall(r'href="(/[^"#?]*)', open(f, encoding="utf-8").read()):
            target = os.path.join(ROOT, href.strip("/"))
            if not (os.path.exists(os.path.join(target, "index.html")) or os.path.isfile(target)):
                probs.append(f"{os.path.relpath(f, ROOT)}: broken link {href}")
    return sorted(set(probs))

def check_css():
    probs=[]
    css = os.path.join(ROOT, "assets", "css", "styles.css")
    if os.path.exists(css):
        for h in set(re.findall(r"#[0-9a-fA-F]{3,6}\b", open(css).read())):
            if h.lower() not in ALLOWED_HEX: probs.append(f"styles.css uses a color outside the system: {h}")
    return probs

if __name__ == "__main__":
    only = sys.argv[1:]
    total = 0
    for md in md_files():
        if only and not any(os.path.basename(md).startswith(o) for o in only): continue
        url, probs = check_page(md)
        total += len(probs)
        print(("PASS  " if not probs else "FAIL  ") + url)
        for p in probs: print("      - " + p)
    if not only:
        for label, probs in [("LINKS", check_links()), ("CSS", check_css())]:
            total += len(probs)
            print(("PASS  " if not probs else "FAIL  ") + label)
            for p in probs[:40]: print("      - " + p)
    print("\nAll checks passed." if total == 0 else f"\n{total} problems found. Fix them and run again.")
    sys.exit(1 if total else 0)
