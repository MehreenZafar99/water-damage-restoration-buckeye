#!/usr/bin/env python3
"""Build guide pages matching service layout plus guide-layout TOC."""
import glob
import json
import os
import re
import sys

from build_services import (
    DOMAIN,
    PHONE,
    SERVICES_NAV,
    TEL,
    esc,
    faq_schema,
    inline,
    link_cards,
    service_nav,
    slug,
)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

AREAS_NAV = [
    ("verrado", "Verrado"),
    ("sundance", "Sundance"),
    ("tartesso", "Tartesso"),
    ("festival-ranch", "Festival Ranch"),
    ("sun-city-festival", "Sun City Festival"),
    ("westpark", "Westpark"),
    ("blue-horizons", "Blue Horizons"),
    ("downtown-buckeye", "Historic Downtown Buckeye"),
    ("teravalis", "Teravalis"),
    ("riata-west", "Riata West"),
    ("watson-estates", "Watson Estates"),
    ("sienna-hills", "Sienna Hills"),
    ("valencia", "Valencia"),
    ("trillium", "Trillium"),
]

BREADCRUMB = {
    "/water-damage-cost-buckeye/": "Water damage cost",
    "/insurance-claim-guide/": "Insurance claim guide",
    "/first-24-hours-after-water-damage/": "First 24 hours",
    "/monsoon-water-damage-guide/": "Monsoon water damage",
}


def tick_heading(text):
    hay = text.lower()
    keys = (
        "checklist",
        "what to do",
        "what not",
        "during a storm",
        "before the season",
        "before monsoon",
        "mistakes to avoid",
        "do this first",
        "prep",
        "quick checklist",
    )
    return any(key in hay for key in keys)


def parse_guide_md(path):
    raw = open(path, encoding="utf-8").read()
    meta = {}
    for key, label in [("URL", "url"), ("Title tag", "title"), ("Meta description", "description"), ("H1", "h1")]:
        m = re.search(rf"\*\*{key}:\*\*\s*(.+)", raw)
        meta[label] = m.group(1).strip()
    body = raw.split("\n---\n", 1)[1]
    intro = ""
    notes = []
    sections = []
    current = None
    list_type = None
    list_items = []

    def flush():
        nonlocal list_type, list_items
        if list_type and current is not None:
            current["blocks"].append((list_type, list_items[:]))
        list_type = None
        list_items = []

    for line in body.splitlines():
        s = line.strip()
        if not s or s == "---":
            flush()
            continue
        if s.startswith("**Intro:**"):
            flush()
            intro = s.split(":**", 1)[1].strip()
            continue
        if s.startswith("**Hero") or s.startswith("**Buttons"):
            continue
        if s.startswith("*") and s.endswith("*") and not s.startswith("**"):
            flush()
            notes.append(s.strip("*").strip())
            continue
        if s.startswith("## "):
            flush()
            current = {"h2": s[3:].strip(), "blocks": []}
            sections.append(current)
            continue
        if s.startswith("### "):
            flush()
            current["blocks"].append(("h3", s[4:].strip()))
            continue
        num = re.match(r"\d+\.\s+(.*)", s)
        if num:
            if list_type not in (None, "ol"):
                flush()
            list_type = "ol"
            list_items.append(num.group(1).strip())
            continue
        if s.startswith("- "):
            if list_type not in (None, "ul"):
                flush()
            list_type = "ul"
            list_items.append(s[2:].strip())
            continue
        flush()
        current["blocks"].append(("p", s))
    flush()
    return meta, intro, notes, sections


def render_blocks(blocks, ticks=False):
    out = []
    for kind, data in blocks:
        if kind == "h3":
            out.append(f"<h3>{inline(data)}</h3>")
        elif kind == "ol":
            lis = "".join(f"<li>{inline(item)}</li>" for item in data)
            out.append(f'<ol class="steps">{lis}</ol>')
        elif kind == "ul":
            cls = "ticks" if ticks else "plain"
            lis = "".join(f"<li>{inline(item)}</li>" for item in data)
            out.append(f'<ul class="{cls}">{lis}</ul>')
        elif kind == "p":
            out.append(f"<p>{inline(data)}</p>")
    return "".join(out)


def faq_html(blocks):
    items = []
    current = None
    for kind, data in blocks:
        if kind == "h3":
            current = {"q": data, "a": []}
            items.append(current)
        elif current is not None:
            current["a"].append((kind, data))
    parts = []
    for item in items:
        body = render_blocks(item["a"])
        parts.append(f'<details class="faq"><summary>{inline(item["q"])}</summary>{body}</details>')
    return "".join(parts), items


def area_nav():
    return "".join(f'<a href="/areas/{s}/">{esc(l)}</a>' for s, l in AREAS_NAV)


def nav_cost_current(url):
    cur = ' aria-current="page"' if url == "/water-damage-cost-buckeye/" else ""
    return f'<a href="/water-damage-cost-buckeye/"{cur}>Cost</a>'


def render_page(meta, intro, notes, sections):
    url = meta["url"]
    bc = BREADCRUMB[url]
    faq_section = None
    cta_section = None
    for section in reversed(sections):
        if section["h2"].rstrip().endswith("?"):
            cta_section = section
            break
    body_sections = []
    faq_items = []
    idx = 0
    toc_sections = []
    for section in sections:
        h2 = section["h2"]
        if section is cta_section:
            continue
        if h2.lower() == "frequently asked questions":
            faq_section = section
            toc_sections.append(section)
            continue
        toc_sections.append(section)
        klass = "section alt" if idx % 2 else "section"
        idx += 1
        inner = render_blocks(section["blocks"], ticks=tick_heading(h2))
        if h2.lower() == "quick answer":
            inner = f'<div class="panel">{inner}</div>'
        body_sections.append(
            f'<section class="{klass}"><div class="wrap"><h2 id="{slug(h2)}">{esc(h2)}</h2>{inner}</div></section>'
        )

    if faq_section:
        klass = "section alt" if idx % 2 else "section"
        faq_body, faq_items = faq_html(faq_section["blocks"])
        body_sections.append(
            f'<section class="{klass}"><div class="wrap"><h2 id="{slug(faq_section["h2"])}">{esc(faq_section["h2"])}</h2>{faq_body}</div></section>'
        )

    cta_html = ""
    if cta_section:
        cta_body = render_blocks(cta_section["blocks"])
        if "btn-call" not in cta_body:
            cta_body += f'<div class="btn-row"><a class="btn btn-saffron btn-call" href="{TEL}">Call {PHONE}</a></div>'
        cta_html = f'<section class="cta"><div class="wrap"><h2>{esc(cta_section["h2"])}</h2>{cta_body}</div></section>'

    toc_items = "".join(
        f'<li><a href="#{slug(s["h2"])}">{esc(s["h2"])}</a></li>' for s in toc_sections
    )
    notes_html = "".join(f'<p class="note">{inline(n)}</p>' for n in notes)
    guide_body = f'<div class="wrap guide-layout"><nav class="toc" aria-label="On this page"><ol>{toc_items}</ol></nav><div>{"".join(body_sections)}{cta_html}</div></div>'

    graph = [
        {
            "@type": "Article",
            "headline": meta["h1"],
            "datePublished": "2026-09-25",
            "dateModified": "2026-09-25",
            "mainEntityOfPage": DOMAIN + url,
            "author": {"@type": "Organization", "name": "White Tank Water Restoration", "url": DOMAIN + "/"},
            "publisher": {"@type": "Organization", "name": "White Tank Water Restoration", "url": DOMAIN + "/"},
        },
        {
            "@type": "BreadcrumbList",
            "itemListElement": [
                {"@type": "ListItem", "position": 1, "name": "Home", "item": DOMAIN + "/"},
                {"@type": "ListItem", "position": 2, "name": bc, "item": DOMAIN + url},
            ],
        },
    ]
    if faq_items:
        graph.insert(1, {"@type": "FAQPage", "mainEntity": faq_schema(faq_items)})

    schema = json.dumps({"@context": "https://schema.org", "@graph": graph}, ensure_ascii=False).replace("<", "\\u003c")
    print_class = " print-guide" if url == "/first-24-hours-after-water-damage/" else ""

    return f"""<!DOCTYPE html>
<html lang="en-US">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{esc(meta["title"])}</title>
  <meta name="description" content="{esc(meta["description"])}">
  <link rel="canonical" href="{DOMAIN}{url}">
  <meta property="og:type" content="article">
  <meta property="og:title" content="{esc(meta["title"])}">
  <meta property="og:description" content="{esc(meta["description"])}">
  <meta property="og:url" content="{DOMAIN}{url}">
  <meta property="og:image" content="{DOMAIN}/assets/img/og-image.jpg">
  <meta property="og:image:width" content="1200">
  <meta property="og:image:height" content="630">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="{esc(meta["title"])}">
  <meta name="twitter:description" content="{esc(meta["description"])}">
  <meta name="twitter:image" content="{DOMAIN}/assets/img/og-image.jpg">
  <link rel="icon" href="/favicon.svg" type="image/svg+xml">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Source+Sans+3:wght@400;600;700&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="/assets/css/styles.css">
  <!-- analytics -->
  <script type="application/ld+json">{schema}</script>
</head>
<body class="guide{print_class}">
    <a class="skip" href="#main">Skip to content</a>
  <header class="site-header">
    <div class="wrap header-inner">
      <a class="logo" href="/">
        <svg width="40" height="28" viewBox="0 0 40 28" aria-hidden="true"><path fill="#5B1E2D" d="M0 26 L8 14 L14 20 L22 6 L30 16 L40 10 L40 26 Z"/></svg>
        <span>White Tank Water Restoration</span>
      </a>
      <button class="nav-toggle" id="nav-toggle" type="button" aria-expanded="false" aria-controls="site-nav">Menu</button>
      <nav class="site-nav" id="site-nav" aria-label="Primary">
        <div class="nav-drop">
          <button type="button" aria-expanded="false" aria-controls="menu-services" aria-haspopup="true">Services</button>
          <div class="dropdown" id="menu-services">{service_nav("")}</div>
        </div>
        <div class="nav-drop">
          <button type="button" aria-expanded="false" aria-controls="menu-areas" aria-haspopup="true">Areas</button>
          <div class="dropdown" id="menu-areas">{area_nav()}</div>
        </div>
        {nav_cost_current(url)}
        <a href="/about/">About</a>
        <a href="/contact/">Contact</a>
      </nav>
      <a class="btn btn-saffron header-call" href="{TEL}">Call {PHONE}</a>
    </div>
  </header>
  <nav class="crumbs" aria-label="Breadcrumb"><div class="wrap"><ol><li><a href="/">Home</a></li><li>{esc(bc)}</li></ol></div></nav>
  <main id="main">
    <header class="hero"><div class="wrap" id="request"><div class="hero-copy"><h1>{esc(meta["h1"])}</h1><p class="lead">{inline(intro)}</p>{notes_html}<div class="btn-row"><a class="btn btn-saffron btn-call" href="{TEL}">Call {PHONE}</a></div></div></div></header>
    {guide_body}
  </main>
  <footer class="site-footer">
    <div class="wrap">
      <p class="footer-lead">White Tank Water Restoration helps Buckeye homes and businesses recover from water damage, day or night.</p>
      <div class="footer-grid">
        <div><h2>Services</h2><ul>{"".join(f'<li><a href="/services/{s}/">{esc(l)}</a></li>' for s, l in SERVICES_NAV)}</ul></div>
        <div><h2>Areas</h2><ul>{"".join(f'<li><a href="/areas/{s}/">{esc(l)}</a></li>' for s, l in AREAS_NAV)}</ul></div>
        <div><h2>Guides</h2><ul><li><a href="/water-damage-cost-buckeye/">Water damage cost</a></li><li><a href="/insurance-claim-guide/">Insurance claim guide</a></li><li><a href="/first-24-hours-after-water-damage/">First 24 hours</a></li><li><a href="/monsoon-water-damage-guide/">Monsoon water damage</a></li><li><a href="/faq/">FAQ</a></li></ul></div>
        <div>
          <h2>Contact</h2>
          <ul>
            <li><a href="{TEL}">{PHONE}</a></li>
            <li>Serving Buckeye, AZ 85326 and 85396</li>
            <li>Open 24/7</li>
          </ul>
        </div>
      </div>
      <div class="footer-base">
        <a href="/privacy-policy/">Privacy Policy</a>
        <a href="/terms-of-service/">Terms of Service</a>
        <span>© <span id="year"></span> White Tank Water Restoration</span>
      </div>
    </div>
  </footer>
  <div class="sticky-bar">
    <a class="btn btn-saffron btn-call" href="{TEL}">Call {PHONE}</a>
  </div>
  <script src="/assets/js/main.js" defer></script>
</body>
</html>
"""


def build(files):
    for name in files:
        path = os.path.join(ROOT, "content", "batch-2", name)
        meta, intro, notes, sections = parse_guide_md(path)
        slug_dir = meta["url"].strip("/")
        out_dir = os.path.join(ROOT, slug_dir)
        os.makedirs(out_dir, exist_ok=True)
        html_doc = render_page(meta, intro, notes, sections)
        with open(os.path.join(out_dir, "index.html"), "w", encoding="utf-8") as f:
            f.write(html_doc)
        print("built", meta["url"])


if __name__ == "__main__":
    if len(sys.argv) > 1:
        batch_dir = os.path.join(ROOT, "content", "batch-2")
        selected = []
        for arg in sys.argv[1:]:
            if arg.endswith(".md"):
                selected.append(arg)
            elif arg.isdigit():
                matches = sorted(glob.glob(os.path.join(batch_dir, f"{arg.zfill(2)}-*.md")))
                selected.extend(os.path.basename(p) for p in matches)
            else:
                matches = sorted(glob.glob(os.path.join(batch_dir, f"*{arg}*.md")))
                selected.extend(os.path.basename(p) for p in matches)
        build(selected)
    else:
        build([])
