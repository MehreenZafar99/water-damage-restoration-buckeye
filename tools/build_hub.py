#!/usr/bin/env python3
"""Build hub pages (services index, areas index) from batch markdown."""
import glob
import json
import os
import re
import sys

from build_services import (
    DOMAIN,
    PHONE,
    TEL,
    esc,
    faq_html,
    faq_schema,
    inline,
    parse_md,
    render_blocks,
    service_nav,
    slug,
)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def parse_hub_md(path):
    raw = open(path, encoding="utf-8").read()
    meta = {}
    for key, label in [("URL", "url"), ("Title tag", "title"), ("Meta description", "description"), ("H1", "h1")]:
        m = re.search(rf"\*\*{key}:\*\*\s*(.+)", raw)
        meta[label] = m.group(1).strip()
    body = raw.split("\n---\n", 1)[1]
    intro = []
    rest_lines = []
    for line in body.splitlines():
        s = line.strip()
        if s.startswith("## "):
            rest_lines.append(line)
        elif s and not s.startswith("**Hero") and not s.startswith("**Buttons"):
            if not rest_lines:
                intro.append(s)
            else:
                rest_lines.append(line)
    tmp = os.path.join(ROOT, "content", "batch-1", "_hub_tmp.md")
    fake = (
        f"# tmp\n\n**URL:** {meta['url']}\n**Title tag:** {meta['title']}\n"
        f"**Meta description:** {meta['description']}\n**H1:** {meta['h1']}\n\n---\n\n"
        + "\n".join(rest_lines)
    )
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(fake)
    try:
        _, _, sections = parse_md(tmp)
    finally:
        os.remove(tmp)
    return meta, intro, sections


def hub_link_card(item):
    m = re.match(r"\*\*\[([^\]]+)\]\(([^)]+)\)\.\*\*\s*(.*)", item.strip())
    if m:
        title, href, desc = m.group(1), m.group(2), m.group(3)
        return f'<a class="link-card" href="{esc(href)}"><strong>{esc(title)}.</strong> {inline(desc)}</a>'
    m = re.search(r"\[([^\]]+)\]\(([^)]+)\)", item)
    if m:
        return f'<a class="link-card" href="{esc(m.group(2))}">{inline(item)}</a>'
    return f'<div class="link-card">{inline(item)}</div>'


def hub_cards(items):
    return f'<div class="card-grid">{"".join(hub_link_card(item) for item in items)}</div>'


def cta_section_for(sections):
    for section in reversed(sections):
        if section["h2"].rstrip().endswith("?"):
            return section
    return None


def render_hub(meta, intro, sections, body_class="services-hub", hub_kind="services"):
    faq_section = None
    cta = cta_section_for(sections)
    body_sections = []
    faq_items = []
    idx = 0
    for section in sections:
        h2 = section["h2"]
        if section is cta:
            continue
        if h2.lower() == "frequently asked questions":
            faq_section = section
            continue
        klass = "section alt" if idx % 2 else "section"
        idx += 1
        inner = ""
        ul_blocks = [b for b in section["blocks"] if b[0] == "ul"]
        if ul_blocks and all(
            re.match(r"\*\*\[", item.strip()) for item in ul_blocks[0][1]
        ):
            inner = hub_cards(ul_blocks[0][1])
            for kind, data in section["blocks"]:
                if kind == "p":
                    inner += f"<p>{inline(data)}</p>"
        else:
            inner = render_blocks(section["blocks"])
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
    if cta:
        cta_body = render_blocks(cta["blocks"])
        if "btn-call" not in cta_body:
            cta_body += f'<div class="btn-row"><a class="btn btn-saffron btn-call" href="{TEL}">Call {PHONE}</a></div>'
        cta_html = f'<section class="cta"><div class="wrap"><h2>{esc(cta["h2"])}</h2>{cta_body}</div></section>'

    intro_html = "".join(f"<p>{inline(p)}</p>" for p in intro)
    if hub_kind == "areas":
        crumbs_html = '<nav class="crumbs" aria-label="Breadcrumb"><div class="wrap"><ol><li><a href="/">Home</a></li><li>Areas</li></ol></div></nav>'
        graph = [
            {
                "@type": "BreadcrumbList",
                "itemListElement": [
                    {"@type": "ListItem", "position": 1, "name": "Home", "item": DOMAIN + "/"},
                    {"@type": "ListItem", "position": 2, "name": "Areas", "item": DOMAIN + "/areas/"},
                ],
            },
        ]
    else:
        crumbs_html = '<nav class="crumbs" aria-label="Breadcrumb"><div class="wrap"><ol><li><a href="/">Home</a></li><li>Services</li></ol></div></nav>'
        graph = [
            {
                "@type": "BreadcrumbList",
                "itemListElement": [
                    {"@type": "ListItem", "position": 1, "name": "Home", "item": DOMAIN + "/"},
                    {"@type": "ListItem", "position": 2, "name": "Services", "item": DOMAIN + "/services/"},
                ],
            },
        ]
    if faq_items:
        graph.insert(0, {"@type": "FAQPage", "mainEntity": faq_schema(faq_items)})

    schema = json.dumps({"@context": "https://schema.org", "@graph": graph}, ensure_ascii=False).replace("<", "\\u003c")
    url = meta["url"]

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
<body class="{body_class}">
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
          <div class="dropdown" id="menu-areas"><a href="/areas/verrado/">Verrado</a><a href="/areas/sundance/">Sundance</a><a href="/areas/tartesso/">Tartesso</a><a href="/areas/festival-ranch/">Festival Ranch</a><a href="/areas/sun-city-festival/">Sun City Festival</a><a href="/areas/westpark/">Westpark</a><a href="/areas/blue-horizons/">Blue Horizons</a><a href="/areas/downtown-buckeye/">Historic Downtown Buckeye</a><a href="/areas/teravalis/">Teravalis</a><a href="/areas/riata-west/">Riata West</a><a href="/areas/watson-estates/">Watson Estates</a><a href="/areas/sienna-hills/">Sienna Hills</a><a href="/areas/valencia/">Valencia</a><a href="/areas/trillium/">Trillium</a></div>
        </div>
        <a href="/water-damage-cost-buckeye/">Cost</a>
        <a href="/about/">About</a>
        <a href="/contact/">Contact</a>
      </nav>
      <a class="btn btn-saffron header-call" href="{TEL}">Call {PHONE}</a>
    </div>
  </header>
  {crumbs_html}
  <main id="main">
    <header class="hero"><div class="wrap" id="request"><div class="hero-copy"><h1>{esc(meta["h1"])}</h1>{intro_html}</div></div></header>
    {"".join(body_sections)}
    {cta_html}
  </main>
  <footer class="site-footer">
    <div class="wrap">
      <p class="footer-lead">White Tank Water Restoration helps Buckeye homes and businesses recover from water damage, day or night.</p>
      <div class="footer-grid">
        <div><h2>Services</h2><ul><li><a href="/services/emergency-water-removal/">Emergency water removal</a></li><li><a href="/services/flood-damage-cleanup/">Flood damage cleanup</a></li><li><a href="/services/burst-pipe-cleanup/">Burst pipe cleanup</a></li><li><a href="/services/slab-leak-water-damage/">Slab leak water damage</a></li><li><a href="/services/water-heater-leak-cleanup/">Water heater leak cleanup</a></li><li><a href="/services/ac-leak-water-damage/">AC leak water damage</a></li><li><a href="/services/ceiling-roof-leak-damage/">Ceiling and roof leak damage</a></li><li><a href="/services/appliance-leak-cleanup/">Washer, dishwasher and fridge leaks</a></li><li><a href="/services/toilet-overflow-cleanup/">Toilet overflow cleanup</a></li><li><a href="/services/sewage-backup-cleanup/">Sewage backup cleanup</a></li><li><a href="/services/structural-drying/">Structural drying</a></li><li><a href="/services/carpet-floor-water-damage/">Wet carpet and floors</a></li><li><a href="/services/mold-remediation/">Mold remediation</a></li><li><a href="/services/storm-damage-restoration/">Storm damage restoration</a></li><li><a href="/services/new-construction-water-damage/">New construction water damage</a></li><li><a href="/services/commercial-water-damage/">Commercial water damage</a></li></ul></div>
        <div><h2>Areas</h2><ul><li><a href="/areas/verrado/">Verrado</a></li><li><a href="/areas/sundance/">Sundance</a></li><li><a href="/areas/tartesso/">Tartesso</a></li><li><a href="/areas/festival-ranch/">Festival Ranch</a></li><li><a href="/areas/sun-city-festival/">Sun City Festival</a></li><li><a href="/areas/westpark/">Westpark</a></li><li><a href="/areas/blue-horizons/">Blue Horizons</a></li><li><a href="/areas/downtown-buckeye/">Historic Downtown Buckeye</a></li><li><a href="/areas/teravalis/">Teravalis</a></li><li><a href="/areas/riata-west/">Riata West</a></li><li><a href="/areas/watson-estates/">Watson Estates</a></li><li><a href="/areas/sienna-hills/">Sienna Hills</a></li><li><a href="/areas/valencia/">Valencia</a></li><li><a href="/areas/trillium/">Trillium</a></li></ul></div>
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


def build_services_hub():
    path = os.path.join(ROOT, "content", "batch-1", "02-services-hub.md")
    meta, intro, sections = parse_hub_md(path)
    doc = render_hub(meta, intro, sections, body_class="services-hub", hub_kind="services")
    out_dir = os.path.join(ROOT, "services")
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "index.html"), "w", encoding="utf-8") as f:
        f.write(doc)
    print("built", meta["url"])


def build_areas_hub():
    path = os.path.join(ROOT, "content", "batch-1", "19-areas-hub.md")
    meta, intro, sections = parse_hub_md(path)
    doc = render_hub(meta, intro, sections, body_class="areas-hub", hub_kind="areas")
    out_dir = os.path.join(ROOT, "areas")
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "index.html"), "w", encoding="utf-8") as f:
        f.write(doc)
    print("built", meta["url"])


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] in ("19", "areas"):
        build_areas_hub()
    elif len(sys.argv) > 1 and sys.argv[1] in ("02", "services"):
        build_services_hub()
    else:
        build_services_hub()
        build_areas_hub()
