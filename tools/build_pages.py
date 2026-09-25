#!/usr/bin/env python3
"""Build about, contact, FAQ, legal pages and 404.html."""
import glob
import html
import json
import os
import re
import sys

from build_guides import AREAS_NAV, area_nav
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

BREADCRUMB = {
    "/about/": "About",
    "/contact/": "Contact",
    "/faq/": "FAQ",
    "/privacy-policy/": "Privacy policy",
    "/terms-of-service/": "Terms of service",
}


def parse_sections(path):
    raw = open(path, encoding="utf-8").read()
    meta = {}
    for key, label in [("URL", "url"), ("Title tag", "title"), ("Meta description", "description"), ("H1", "h1")]:
        m = re.search(rf"\*\*{key}:\*\*\s*(.+)", raw)
        meta[label] = m.group(1).strip()
    body = raw.split("\n---\n", 1)[1]
    pre = []
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
        if s.startswith("*(Developer note"):
            flush()
            continue
        if re.match(r"\*\*Buttons?:\*\*", s):
            flush()
            continue
        if s.startswith("## "):
            flush()
            current = {"h2": s[3:].strip(), "blocks": []}
            sections.append(current)
            continue
        if s.startswith("### "):
            flush()
            if current is None:
                pre.append(("h3", s[4:].strip()))
            else:
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
        if current is None:
            if s.startswith("**") and s.endswith("**") and s != f"**{PHONE}**":
                pre.append(("p", s))
            elif s == f"**{PHONE}**":
                pre.append(("phone", PHONE))
            else:
                pre.append(("p", s))
        else:
            if s == f"**{PHONE}**":
                current["blocks"].append(("phone", PHONE))
            else:
                current["blocks"].append(("p", s))
    flush()
    return meta, pre, sections


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
        elif kind == "phone":
            out.append(f'<p class="phone-xl"><a href="{TEL}">{PHONE}</a></p>')
        elif kind == "p":
            if data.startswith("**") and data.endswith("**"):
                out.append(f"<p><strong>{inline(data.strip('*'))}</strong></p>")
            else:
                out.append(f"<p>{inline(data)}</p>")
    return "".join(out)


def how_we_work_cards(blocks):
    cards = []
    current = None
    for kind, data in blocks:
        if kind == "h3":
            current = {"h": data, "blocks": []}
            cards.append(current)
        elif current is not None:
            current["blocks"].append((kind, data))
    parts = []
    for card in cards:
        parts.append(f"<article><h3>{inline(card['h'])}</h3>{render_blocks(card['blocks'])}</article>")
    return f'<div class="two-col">{"".join(parts)}</div>'


def faq_group_html(blocks):
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


def form_html():
    return f'''<form id="lead-form" method="post" action="{esc("https://FORM_ENDPOINT_PLACEHOLDER")}" novalidate>
        <label>Name
          <input name="name" type="text" autocomplete="name" required>
        </label>
        <label>Phone
          <input name="phone" type="tel" autocomplete="tel" required>
        </label>
        <label>Email
          <input name="email" type="email" autocomplete="email">
        </label>
        <label>Property type
          <select name="property_type" required>
            <option value="">Select one</option>
            <option>Home</option>
            <option>Rental property</option>
            <option>Business</option>
            <option>Other</option>
          </select>
        </label>
        <label>What happened
          <select name="what_happened" required>
            <option value="">Select one</option>
            <option>Burst pipe</option>
            <option>Slab leak</option>
            <option>Water heater</option>
            <option>AC leak</option>
            <option>Appliance</option>
            <option>Toilet or sewage</option>
            <option>Flooding or storm</option>
            <option>Roof or ceiling</option>
            <option>Not sure</option>
          </select>
        </label>
        <label>Neighborhood
          <input name="neighborhood" type="text" autocomplete="address-level3">
        </label>
        <label>Message
          <textarea name="message"></textarea>
        </label>
        <input type="hidden" name="source_page" value="">
        <label class="hp">Website
          <input name="website" type="text" tabindex="-1" autocomplete="off">
        </label>
        <button class="btn btn-saffron" type="submit">Send my request</button>
        <p class="form-status" id="form-status" role="status"></p>
      </form>'''


def footer_html():
    return f"""  <footer class="site-footer">
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
  </div>"""


def header_html(active_about=False, active_contact=False, active_faq=False):
    about_cur = ' aria-current="page"' if active_about else ""
    contact_cur = ' aria-current="page"' if active_contact else ""
    faq_cur = ' aria-current="page"' if active_faq else ""
    return f"""  <header class="site-header">
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
        <a href="/water-damage-cost-buckeye/">Cost</a>
        <a href="/about/"{about_cur}>About</a>
        <a href="/contact/"{contact_cur}>Contact</a>
      </nav>
      <a class="btn btn-saffron header-call" href="{TEL}">Call {PHONE}</a>
    </div>
  </header>"""


def page_shell(meta, body_class, bc, graph, main_html, robots="", active_nav=None):
    active_nav = active_nav or {}
    schema = json.dumps({"@context": "https://schema.org", "@graph": graph}, ensure_ascii=False).replace("<", "\\u003c")
    robots_tag = f'\n  <meta name="robots" content="{robots}">' if robots else ""
    crumbs_html = (
        f'  <nav class="crumbs" aria-label="Breadcrumb"><div class="wrap"><ol><li><a href="/">Home</a></li><li>{esc(bc)}</li></ol></div></nav>'
        if bc
        else ""
    )
    return f"""<!DOCTYPE html>
<html lang="en-US">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{esc(meta["title"])}</title>
  <meta name="description" content="{esc(meta["description"])}">
  <link rel="canonical" href="{DOMAIN}{meta["url"]}">{robots_tag}
  <meta property="og:type" content="website">
  <meta property="og:title" content="{esc(meta["title"])}">
  <meta property="og:description" content="{esc(meta["description"])}">
  <meta property="og:url" content="{DOMAIN}{meta["url"]}">
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
{header_html(**active_nav)}
{crumbs_html}
  <main id="main">
{main_html}
  </main>
{footer_html()}
  <script src="/assets/js/main.js" defer></script>
</body>
</html>
"""


def build_about(path):
    meta, pre, sections = parse_sections(path)
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
        if h2.lower() == "how we work":
            inner = how_we_work_cards(section["blocks"])
        else:
            inner = render_blocks(section["blocks"])
        body_sections.append(
            f'<section class="{klass}"><div class="wrap"><h2 id="{slug(h2)}">{esc(h2)}</h2>{inner}</div></section>'
        )
    if faq_section:
        klass = "section alt" if idx % 2 else "section"
        faq_body, faq_items = faq_group_html(faq_section["blocks"])
        body_sections.append(
            f'<section class="{klass}"><div class="wrap"><h2 id="{slug(faq_section["h2"])}">{esc(faq_section["h2"])}</h2>{faq_body}</div></section>'
        )
    cta_html = ""
    if cta_section:
        cta_body = render_blocks(cta_section["blocks"])
        if "btn-call" not in cta_body:
            cta_body += f'<div class="btn-row"><a class="btn btn-saffron btn-call" href="{TEL}">Call {PHONE}</a></div>'
        cta_html = f'<section class="cta"><div class="wrap"><h2>{esc(cta_section["h2"])}</h2>{cta_body}</div></section>'
    main = f'    <header class="hero"><div class="wrap" id="request"><div class="hero-copy"><h1>{esc(meta["h1"])}</h1><div class="btn-row"><a class="btn btn-saffron btn-call" href="{TEL}">Call {PHONE}</a></div></div></div></header>\n    {"".join(body_sections)}{cta_html}'
    graph = [
        {"@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Home", "item": DOMAIN + "/"},
            {"@type": "ListItem", "position": 2, "name": "About", "item": DOMAIN + meta["url"]},
        ]},
    ]
    if faq_items:
        graph.insert(0, {"@type": "FAQPage", "mainEntity": faq_schema(faq_items)})
    return page_shell(meta, "about", BREADCRUMB[meta["url"]], graph, main, active_nav={"active_about": True})


def build_contact(path):
    meta, pre, sections = parse_sections(path)
    body_sections = []
    idx = 0
    for section in sections:
        h2 = section["h2"]
        klass = "section alt" if idx % 2 else "section"
        idx += 1
        if h2.lower() == "send us a request":
            inner = render_blocks(section["blocks"])
            body_sections.append(
                f'<section class="{klass}"><div class="wrap"><div class="form-card" id="request"><h2>{esc(h2)}</h2>{inner}{form_html()}</div></div></section>'
            )
        elif h2.lower() == "before we arrive, do this first":
            inner = f'<div class="panel">{render_blocks(section["blocks"])}</div>'
            body_sections.append(
                f'<section class="{klass}"><div class="wrap"><h2 id="{slug(h2)}">{esc(h2)}</h2>{inner}</div></section>'
            )
        elif h2.lower() == "water damage right now? call us.":
            inner = render_blocks(section["blocks"])
            inner += f'<div class="btn-row"><a class="btn btn-saffron btn-call" href="{TEL}">Call {PHONE}</a></div>'
            body_sections.append(
                f'<section class="{klass}"><div class="wrap"><h2 id="{slug(h2)}">{esc(h2)}</h2>{inner}</div></section>'
            )
        else:
            inner = render_blocks(section["blocks"])
            body_sections.append(
                f'<section class="{klass}"><div class="wrap"><h2 id="{slug(h2)}">{esc(h2)}</h2>{inner}</div></section>'
            )
    main = f'    <header class="hero"><div class="wrap"><div class="hero-copy"><h1>{esc(meta["h1"])}</h1></div></div></header>\n    {"".join(body_sections)}'
    graph = [
        {"@type": "ContactPage", "name": meta["h1"], "url": DOMAIN + meta["url"]},
        {"@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Home", "item": DOMAIN + "/"},
            {"@type": "ListItem", "position": 2, "name": "Contact", "item": DOMAIN + meta["url"]},
        ]},
    ]
    return page_shell(meta, "contact", BREADCRUMB[meta["url"]], graph, main, active_nav={"active_contact": True})


def build_faq(path):
    meta, pre, sections = parse_sections(path)
    intro = "".join(render_blocks([b]) for b in pre if b[0] == "p")
    cta_section = None
    for section in reversed(sections):
        if section["h2"].rstrip().endswith("?"):
            cta_section = section
            break
    body_sections = []
    faq_items = []
    idx = 0
    for section in sections:
        if section is cta_section:
            continue
        klass = "section alt" if idx % 2 else "section"
        idx += 1
        h2 = section["h2"]
        group_body, items = faq_group_html(section["blocks"])
        faq_items.extend(items)
        body_sections.append(
            f'<section class="{klass}"><div class="wrap"><div class="faq-group"><h2 id="{slug(h2)}">{esc(h2)}</h2>{group_body}</div></div></section>'
        )
    cta_html = ""
    if cta_section:
        cta_body = render_blocks(cta_section["blocks"])
        cta_body += f'<div class="btn-row"><a class="btn btn-saffron btn-call" href="{TEL}">Call {PHONE}</a></div>'
        cta_html = f'<section class="cta"><div class="wrap"><h2>{esc(cta_section["h2"])}</h2>{cta_body}</div></section>'
    main = f'    <header class="hero"><div class="wrap" id="request"><div class="hero-copy"><h1>{esc(meta["h1"])}</h1>{intro}<div class="btn-row"><a class="btn btn-saffron btn-call" href="{TEL}">Call {PHONE}</a></div></div></div></header>\n    {"".join(body_sections)}{cta_html}'
    graph = [
        {"@type": "FAQPage", "mainEntity": faq_schema(faq_items)},
        {"@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Home", "item": DOMAIN + "/"},
            {"@type": "ListItem", "position": 2, "name": "FAQ", "item": DOMAIN + meta["url"]},
        ]},
    ]
    return page_shell(meta, "faq", BREADCRUMB[meta["url"]], graph, main, active_nav={"active_faq": True})


def build_legal(path):
    meta, pre, sections = parse_sections(path)
    intro = render_blocks([(k, d) for k, d in pre])
    parts = [intro]
    for section in sections:
        parts.append(f'<h2 id="{slug(section["h2"])}">{esc(section["h2"])}</h2>{render_blocks(section["blocks"])}')
    main = f'    <header class="hero"><div class="wrap"><div class="hero-copy"><h1>{esc(meta["h1"])}</h1></div></div></header>\n    <section class="section"><div class="wrap"><article class="prose legal">{"".join(parts)}</article></div></section>'
    graph = [{"@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": 1, "name": "Home", "item": DOMAIN + "/"},
        {"@type": "ListItem", "position": 2, "name": BREADCRUMB[meta["url"]], "item": DOMAIN + meta["url"]},
    ]}]
    return page_shell(meta, "legal", BREADCRUMB[meta["url"]], graph, main)


def build_404():
    meta = {
        "url": "/404.html",
        "title": "Page not found | White Tank Water Restoration",
        "description": "This page is not here. Call White Tank Water Restoration for water damage help in Buckeye.",
        "h1": "This page is not here",
    }
    main = f"""    <header class="hero"><div class="wrap"><div class="hero-copy"><h1>This page is not here</h1><p class="lead">The page you were looking for has moved or does not exist. If you have water damage right now, call us and we will help.</p><div class="btn-row"><a class="btn btn-saffron btn-call" href="{TEL}">Call {PHONE}</a><a class="btn btn-ghost" href="/">Go to the homepage</a></div></div></div></header>
    <section class="section"><div class="wrap"><div class="card-grid"><a class="link-card" href="/services/">Water damage services</a><a class="link-card" href="/areas/">Buckeye service areas</a></div></div></section>"""
    graph = []
    return page_shell(meta, "page", "", graph, main, robots="noindex")


def write_page(meta, html_doc):
    if meta["url"] == "/404.html":
        out = os.path.join(ROOT, "404.html")
    else:
        out = os.path.join(ROOT, meta["url"].strip("/"), "index.html")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        f.write(html_doc)
    print("built", meta["url"])


BUILDERS = {
    "20": lambda p: build_about(p),
    "21": lambda p: build_contact(p),
    "40": lambda p: build_faq(p),
    "41": lambda p: build_legal(p),
    "42": lambda p: build_legal(p),
}


def locate_md(num):
    for batch in ("batch-1", "batch-2"):
        matches = glob.glob(os.path.join(ROOT, "content", batch, f"{num.zfill(2)}-*.md"))
        if matches:
            return matches[0]
    return None


if __name__ == "__main__":
    args = sys.argv[1:] if len(sys.argv) > 1 else ["20", "21", "40", "41", "42"]
    for arg in args:
        if arg == "404":
            write_page({"url": "/404.html"}, build_404())
            continue
        path = locate_md(arg) if arg.isdigit() else arg
        if not path:
            print("missing", arg)
            continue
        num = os.path.basename(path)[:2]
        doc = BUILDERS[num](path)
        meta, _, _ = parse_sections(path)
        write_page(meta, doc)
    if "404" not in args:
        write_page({"url": "/404.html"}, build_404())
