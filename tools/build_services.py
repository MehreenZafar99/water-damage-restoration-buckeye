#!/usr/bin/env python3
"""Build service pages matching services/slab-leak-water-damage/index.html."""
import html
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOMAIN = "https://waterdamagerestorationbuckeyeaz.com"
PHONE = "(623) 555-0148"
TEL = "tel:+16235550148"

SERVICES_NAV = [
    ("emergency-water-removal", "Emergency water removal"),
    ("flood-damage-cleanup", "Flood damage cleanup"),
    ("burst-pipe-cleanup", "Burst pipe cleanup"),
    ("slab-leak-water-damage", "Slab leak water damage"),
    ("water-heater-leak-cleanup", "Water heater leak cleanup"),
    ("ac-leak-water-damage", "AC leak water damage"),
    ("ceiling-roof-leak-damage", "Ceiling and roof leak damage"),
    ("appliance-leak-cleanup", "Washer, dishwasher and fridge leaks"),
    ("toilet-overflow-cleanup", "Toilet overflow cleanup"),
    ("sewage-backup-cleanup", "Sewage backup cleanup"),
    ("structural-drying", "Structural drying"),
    ("carpet-floor-water-damage", "Wet carpet and floors"),
    ("mold-remediation", "Mold remediation"),
    ("storm-damage-restoration", "Storm damage restoration"),
    ("new-construction-water-damage", "New construction water damage"),
    ("commercial-water-damage", "Commercial water damage"),
]

BREADCRUMB = dict(SERVICES_NAV)


def esc(text):
    return html.escape(text, quote=True)


def slug(text):
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def inline(text):
    s = esc(text)
    def link_replace(m):
        text, href, punct = m.group(1), m.group(2), m.group(3) or ""
        if punct:
            return f'<a href="{href}">{text}{punct}</a>'
        return f'<a href="{href}">{text}</a>'

    s = re.sub(r"\[([^\]]+)\]\(([^)]+)\)([,.!?;:])?", link_replace, s)
    s = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(
        re.escape(PHONE) + r"([,.!?;:])?",
        lambda m: f'<a href="{TEL}">{PHONE}{m.group(1) or ""}</a>',
        s,
    )
    return s


def parse_md(path):
    raw = open(path, encoding="utf-8").read()
    meta = {}
    for key, label in [("URL", "url"), ("Title tag", "title"), ("Meta description", "description"), ("H1", "h1")]:
        m = re.search(rf"\*\*{key}:\*\*\s*(.+)", raw)
        meta[label] = m.group(1).strip()
    body = raw.split("\n---\n", 1)[1]
    hero_sub = ""
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
        if s.startswith("**Hero subheading:**"):
            flush()
            hero_sub = s.split(":**", 1)[1].strip()
            continue
        if s.startswith("**Hero") or s.startswith("**Buttons"):
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
    return meta, hero_sub, sections


def render_blocks(blocks):
    out = []
    i = 0
    while i < len(blocks):
        kind, data = blocks[i]
        if kind == "h3":
            out.append(f"<h3>{inline(data)}</h3>")
        elif kind == "ol":
            lis = "".join(f"<li>{inline(item)}</li>" for item in data)
            out.append(f'<ol class="steps">{lis}</ol>')
        elif kind == "ul":
            lis = "".join(f"<li>{inline(item)}</li>" for item in data)
            out.append(f'<ul class="plain">{lis}</ul>')
        elif kind == "p":
            out.append(f"<p>{inline(data)}</p>")
        i += 1
    return "".join(out)


def link_cards(items):
    cards = []
    for item in items:
        m = re.match(r"\[([^\]]+)\]\(([^)]+)\)", item)
        if m:
            cards.append(f'<a class="link-card" href="{esc(m.group(2))}">{esc(m.group(1))}</a>')
    return f'<div class="card-grid">{"".join(cards)}</div>'


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


def faq_schema(items):
    entities = []
    for item in items:
        ans = []
        for kind, data in item["a"]:
            if kind == "p":
                ans.append(re.sub(r"<[^>]+>", "", inline(data)))
            elif kind in ("ul", "ol"):
                for row in data:
                    ans.append(re.sub(r"<[^>]+>", "", inline(row)))
        entities.append({
            "@type": "Question",
            "name": item["q"],
            "acceptedAnswer": {"@type": "Answer", "text": " ".join(ans)},
        })
    return entities


def service_nav(active_slug):
    links = []
    for slug_name, label in SERVICES_NAV:
        href = f"/services/{slug_name}/"
        cur = ' aria-current="page"' if slug_name == active_slug else ""
        links.append(f'<a href="{href}"{cur}>{esc(label)}</a>')
    return "".join(links)


def render_page(meta, hero_sub, sections, active_slug):
    url = meta["url"]
    slug_name = url.strip("/").split("/")[-1]
    bc = BREADCRUMB[slug_name]
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
        inner = ""
        if h2.lower() == "related services":
            ul = next(b for b in section["blocks"] if b[0] == "ul")
            inner = link_cards(ul[1])
        elif h2.lower() == "areas we serve":
            parts = []
            for kind, data in section["blocks"]:
                if kind == "ul":
                    parts.append(link_cards(data))
                elif kind == "p":
                    parts.append(f"<p>{inline(data)}</p>")
            inner = "".join(parts)
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

    cta_h2 = cta_section["h2"]
    cta_blocks = render_blocks(cta_section["blocks"])
    if "btn-call" not in cta_blocks:
        cta_blocks += f'<div class="btn-row"><a class="btn btn-saffron btn-call" href="{TEL}">Call {PHONE}</a></div>'
    cta = f'<section class="cta"><div class="wrap"><h2>{esc(cta_h2)}</h2>{cta_blocks}</div></section>'

    graph = [
        {
            "@type": "Service",
            "name": meta["h1"],
            "serviceType": meta["h1"],
            "url": DOMAIN + url,
            "provider": {"@id": DOMAIN + "/#business"},
            "areaServed": {
                "@type": "City",
                "name": "Buckeye",
                "address": {"@type": "PostalAddress", "addressLocality": "Buckeye", "addressRegion": "AZ", "addressCountry": "US"},
            },
        },
        {
            "@type": "BreadcrumbList",
            "itemListElement": [
                {"@type": "ListItem", "position": 1, "name": "Home", "item": DOMAIN + "/"},
                {"@type": "ListItem", "position": 2, "name": "Services", "item": DOMAIN + "/services/"},
                {"@type": "ListItem", "position": 3, "name": bc, "item": DOMAIN + url},
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
<body class="service">
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
          <div class="dropdown" id="menu-services">{service_nav(active_slug)}</div>
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
  <nav class="crumbs" aria-label="Breadcrumb"><div class="wrap"><ol><li><a href="/">Home</a></li><li><a href="/services/">Services</a></li><li>{esc(bc)}</li></ol></div></nav>
  <main id="main">
    <header class="hero"><div class="wrap" id="request"><div class="hero-copy"><h1>{esc(meta["h1"])}</h1><p class="lead">{inline(hero_sub)}</p><div class="btn-row"><a class="btn btn-saffron btn-call" href="{TEL}">Call {PHONE}</a></div></div></div></header>
    {"".join(body_sections)}
    {cta}
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


def build(files):
    for name in files:
        path = os.path.join(ROOT, "content", "batch-1", name)
        meta, hero_sub, sections = parse_md(path)
        slug_name = meta["url"].strip("/").split("/")[-1]
        out_dir = os.path.join(ROOT, "services", slug_name)
        os.makedirs(out_dir, exist_ok=True)
        html_doc = render_page(meta, hero_sub, sections, slug_name)
        with open(os.path.join(out_dir, "index.html"), "w", encoding="utf-8") as f:
            f.write(html_doc)
        print("built", meta["url"])


if __name__ == "__main__":
    import sys

    default = [
        "03-emergency-water-removal.md",
        "04-flood-damage-cleanup.md",
        "05-burst-pipe-cleanup.md",
        "07-water-heater-leak-cleanup.md",
    ]
    if len(sys.argv) > 1:
        import glob

        batch_dir = os.path.join(ROOT, "content", "batch-1")
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
