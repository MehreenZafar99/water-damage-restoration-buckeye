#!/usr/bin/env python3
"""Build area pages matching services/slab-leak-water-damage/index.html layout."""
import glob
import html
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
    faq_html,
    faq_schema,
    inline,
    link_cards,
    parse_md,
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

AREA_NAMES = dict(AREAS_NAV)


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
        "checkup",
    )
    return any(key in hay for key in keys)


def services_section(h2):
    return h2.lower().startswith("services ") and "call us for most" in h2.lower()


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


def area_nav(active_slug):
    links = []
    for slug_name, label in AREAS_NAV:
        href = f"/areas/{slug_name}/"
        cur = ' aria-current="page"' if slug_name == active_slug else ""
        links.append(f'<a href="{href}"{cur}>{esc(label)}</a>')
    return "".join(links)


def render_page(meta, hero_sub, sections, active_slug):
    url = meta["url"]
    place = AREA_NAMES[active_slug]
    faq_section = None
    cta_section = None
    for section in reversed(sections):
        if section["h2"].rstrip().endswith("?"):
            cta_section = section
            break
    body_sections = []
    faq_items = []
    idx = 0
    for section in sections:
        h2 = section["h2"]
        if section is cta_section:
            continue
        if h2.lower() == "frequently asked questions":
            faq_section = section
            continue
        klass = "section alt" if idx % 2 else "section"
        idx += 1
        if services_section(h2):
            ul = next(b for b in section["blocks"] if b[0] == "ul")
            inner = link_cards(ul[1])
        else:
            inner = render_blocks(section["blocks"], ticks=tick_heading(h2))
        body_sections.append(
            f'<section class="{klass}"><div class="wrap"><h2 id="{slug(h2)}">{esc(h2)}</h2>{inner}</div></section>'
        )

    if faq_section:
        klass = "section alt" if idx % 2 else "section"
        faq_body, faq_items = faq_html(faq_section["blocks"])
        body_sections.append(
            f'<section class="{klass}"><div class="wrap"><h2 id="{slug(faq_section["h2"])}">{esc(faq_section["h2"])}</h2>{faq_body}</div></section>'
        )

    cta_h2 = cta_section["h2"]
    cta_blocks = render_blocks(cta_section["blocks"])
    if "btn-call" not in cta_blocks:
        cta_blocks += f'<div class="btn-row"><a class="btn btn-saffron btn-call" href="{TEL}">Call {PHONE}</a></div>'
    cta = f'<section class="cta"><div class="wrap"><h2>{esc(cta_h2)}</h2>{cta_blocks}</div></section>'

    graph = [
        {
            "@type": "Service",
            "name": meta["h1"],
            "serviceType": "Water damage restoration",
            "url": DOMAIN + url,
            "provider": {"@id": DOMAIN + "/#business"},
            "areaServed": {"@type": "Place", "name": f"{place}, Buckeye, AZ"},
        },
        {
            "@type": "BreadcrumbList",
            "itemListElement": [
                {"@type": "ListItem", "position": 1, "name": "Home", "item": DOMAIN + "/"},
                {"@type": "ListItem", "position": 2, "name": "Areas", "item": DOMAIN + "/areas/"},
                {"@type": "ListItem", "position": 3, "name": place, "item": DOMAIN + url},
            ],
        },
    ]
    if faq_items:
        graph.insert(1, {"@type": "FAQPage", "mainEntity": faq_schema(faq_items)})

    schema = json.dumps({"@context": "https://schema.org", "@graph": graph}, ensure_ascii=False).replace("<", "\\u003c")

    return f"""<!DOCTYPE html>
<html lang="en-US">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{esc(meta["title"])}</title>
  <meta name="description" content="{esc(meta["description"])}">
  <link rel="canonical" href="{DOMAIN}{url}">
  <meta property="og:type" content="website">
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
<body class="area">
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
          <div class="dropdown" id="menu-areas">{area_nav(active_slug)}</div>
        </div>
        <a href="/water-damage-cost-buckeye/">Cost</a>
        <a href="/about/">About</a>
        <a href="/contact/">Contact</a>
      </nav>
      <a class="btn btn-saffron header-call" href="{TEL}">Call {PHONE}</a>
    </div>
  </header>
  <nav class="crumbs" aria-label="Breadcrumb"><div class="wrap"><ol><li><a href="/">Home</a></li><li><a href="/areas/">Areas</a></li><li>{esc(place)}</li></ol></div></nav>
  <main id="main">
    <header class="hero"><div class="wrap" id="request"><div class="hero-copy"><h1>{esc(meta["h1"])}</h1><p class="lead">{inline(hero_sub)}</p><div class="btn-row"><a class="btn btn-saffron btn-call" href="{TEL}">Call {PHONE}</a></div></div></div></header>
    {"".join(body_sections)}
    {cta}
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
        meta, hero_sub, sections = parse_md(path)
        slug_name = meta["url"].strip("/").split("/")[-1]
        out_dir = os.path.join(ROOT, "areas", slug_name)
        os.makedirs(out_dir, exist_ok=True)
        html_doc = render_page(meta, hero_sub, sections, slug_name)
        with open(os.path.join(out_dir, "index.html"), "w", encoding="utf-8") as f:
            f.write(html_doc)
        print("built", meta["url"])


if __name__ == "__main__":
    default = []
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
        build(default)
