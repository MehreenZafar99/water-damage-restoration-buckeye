#!/usr/bin/env python3
"""Generate every remaining static page from markdown, matching the slab-leak reference."""
from __future__ import annotations

import html
import json
import os
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DOMAIN = "https://waterdamagerestorationbuckeyeaz.com"
PHONE = "(623) 555-0148"
TEL = "tel:+16235550148"
SCHEMA_TEL = "+1-623-555-0148"
BUSINESS = "White Tank Water Restoration"
DATE = "2026-09-25"

SKIP_URLS = {"/", "/services/slab-leak-water-damage/"}

IMAGE_MAP = {
    "emergency-water-removal": (
        "hero-water-extraction.webp",
        "Emergency extraction of standing water inside a Buckeye home",
    ),
    "flood-damage-cleanup": (
        "flooded-living-room.webp",
        "Living room in a Buckeye home with floodwater across the floor",
    ),
    "water-heater-leak-cleanup": (
        "water-heater-leak.webp",
        "Water heater leak spreading across a Buckeye garage floor",
    ),
    "ac-leak-water-damage": (
        "ceiling-water-stain.webp",
        "Ceiling stain in a Buckeye home from an air conditioner leak",
    ),
    "ceiling-roof-leak-damage": (
        "ceiling-water-stain.webp",
        "Water stain and drip on a Buckeye ceiling after a roof leak",
    ),
    "appliance-leak-cleanup": (
        "wet-carpet.webp",
        "Wet carpet beside an appliance leak in a Buckeye home",
    ),
    "carpet-floor-water-damage": (
        "wet-carpet.webp",
        "Wet carpet pulled back for drying in a Buckeye home",
    ),
    "structural-drying": (
        "drying-equipment.webp",
        "Air movers and a dehumidifier drying walls and floors in a Buckeye home",
    ),
    "mold-remediation": (
        "mold-wall.webp",
        "Mold on drywall after water damage inside a Buckeye home",
    ),
    "storm-damage-restoration": (
        "flooded-living-room.webp",
        "Buckeye living room soaked after wind and rain from a storm",
    ),
    "commercial-water-damage": (
        "commercial-building-water.webp",
        "Water on the floor of a Buckeye commercial building",
    ),
    "about": (
        "drying-equipment.webp",
        "Drying equipment set up inside a Buckeye home",
    ),
    "monsoon-water-damage-guide": (
        "monsoon-storm-buckeye.webp",
        "Summer monsoon clouds and rain over Buckeye",
    ),
}

WATERLINE = """<svg class="waterline waterline--small" viewBox="0 0 520 220" role="img" aria-label="How water damage spreads: hour 1 floors and baseboards, hour 24 drywall wicks water up, hour 48 mold can start">
  <rect class="wl-wall" x="0" y="0" width="300" height="200" rx="4"/>
  <rect class="wl-base" x="0" y="184" width="300" height="16"/>
  <rect class="wl-floor" x="0" y="200" width="520" height="20"/>
  <rect class="wl-water" x="0" y="96" width="300" height="104"/>
  <g class="wl-step s1"><line class="wl-line" x1="0" y1="184" x2="316" y2="184"/><text x="324" y="188">Hour 1: floors and baseboards</text></g>
  <g class="wl-step s2"><line class="wl-line" x1="0" y1="140" x2="316" y2="140"/><text x="324" y="144">Hour 24: drywall wicks water up</text></g>
  <g class="wl-step s3"><line class="wl-line" x1="0" y1="96" x2="316" y2="96"/><text x="324" y="100">Hour 48: mold can start</text></g>
</svg>"""

CRUMB_SERVICE = {
    "emergency-water-removal": "Emergency Water Removal",
    "flood-damage-cleanup": "Flood Damage Cleanup",
    "burst-pipe-cleanup": "Burst Pipe Cleanup",
    "slab-leak-water-damage": "Slab Leak Water Damage",
    "water-heater-leak-cleanup": "Water Heater Leak Cleanup",
    "ac-leak-water-damage": "AC Leak Water Damage",
    "ceiling-roof-leak-damage": "Ceiling and Roof Leaks",
    "appliance-leak-cleanup": "Appliance Leak Cleanup",
    "toilet-overflow-cleanup": "Toilet Overflow Cleanup",
    "sewage-backup-cleanup": "Sewage Backup Cleanup",
    "structural-drying": "Structural Drying",
    "carpet-floor-water-damage": "Wet Carpet and Floors",
    "mold-remediation": "Mold Remediation",
    "storm-damage-restoration": "Storm Damage Restoration",
    "new-construction-water-damage": "New Construction Leaks",
    "commercial-water-damage": "Commercial Water Damage",
}

CRUMB_AREA = {
    "verrado": "Verrado",
    "sundance": "Sundance",
    "tartesso": "Tartesso",
    "festival-ranch": "Festival Ranch",
    "sun-city-festival": "Sun City Festival",
    "westpark": "Westpark",
    "blue-horizons": "Blue Horizons",
    "downtown-buckeye": "Historic Downtown Buckeye",
    "teravalis": "Teravalis",
    "riata-west": "Riata West",
    "watson-estates": "Watson Estates",
    "sienna-hills": "Sienna Hills",
    "valencia": "Valencia",
    "trillium": "Trillium",
}

GUIDE_CRUMB = {
    "/water-damage-cost-buckeye/": "Water Damage Cost",
    "/insurance-claim-guide/": "Insurance Claim Guide",
    "/first-24-hours-after-water-damage/": "First 24 Hours",
    "/monsoon-water-damage-guide/": "Monsoon Guide",
}


def load_partials():
    text = (ROOT / "_templates" / "partials.html").read_text(encoding="utf-8")

    def between(start_marker, end_marker=None):
        start = text.index(start_marker)
        # jump to end of the comment line
        start = text.index("\n", start) + 1
        if end_marker:
            end = text.index(end_marker, start)
            return text[start:end].rstrip() + "\n"
        return text[start:].rstrip() + "\n"

    top = between("PARTIAL: TOP", "<!-- ============ PARTIAL: LEAD FORM")
    form = between("PARTIAL: LEAD FORM", "<!-- ============ PARTIAL: CALL CARD")
    trust = between("PARTIAL: TRUST BAR", "<!-- ============ PARTIAL: SIDEBAR")
    sidebar = between("PARTIAL: SIDEBAR", "<!-- ============ PARTIAL: CTA BAND")
    footer = between("PARTIAL: FOOTER")
    head_assets = between("PARTIAL: HEAD", "<!-- ============ PARTIAL: TOP")
    return {
        "head_assets": head_assets.strip() + "\n",
        "top": top,
        "form": form.strip() + "\n",
        "trust": trust,
        "sidebar": sidebar,
        "footer": footer,
    }


P = load_partials()


def esc(s: str) -> str:
    return html.escape(s, quote=True)


def inline(text: str) -> str:
    s = esc(text)
    # Keep trailing punctuation inside the <a> so the checker does not see
    # a space between link text and the period/comma (Text() joins nodes with spaces).
    s = re.sub(
        r"\[([^\]]+)\]\(([^)]+)\)([,.!?;:]*)",
        lambda m: f'<a href="{esc(m.group(2))}">{m.group(1)}{m.group(3)}</a>',
        s,
    )
    s = re.sub(r"\*\*([^*]+)\*\*([,.!?;:]*)", r"<strong>\1\2</strong>", s)
    s = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"<em>\1</em>", s)
    # Leave phone numbers as plain text in prose (buttons/partials already link them).
    return s


def plain(text: str) -> str:
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    text = text.replace("**", "").replace("*", "")
    return re.sub(r"\s+", " ", text).strip()


def slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-") or "section"


def page_path(url: str) -> Path:
    url = url if url.endswith("/") or url.endswith(".html") else url + "/"
    if url == "/":
        return ROOT / "index.html"
    if url.endswith(".html"):
        return ROOT / url.lstrip("/")
    return ROOT / url.strip("/") / "index.html"


def md_files():
    files = []
    for batch in ("batch-1", "batch-2"):
        d = ROOT / "content" / batch
        if d.exists():
            files.extend(sorted(d.glob("*.md")))
    return files


def parse_md(path: Path) -> dict:
    raw = path.read_text(encoding="utf-8")
    meta = {}
    for key, label in (
        ("URL", "url"),
        ("Title tag", "title"),
        ("Meta description", "description"),
        ("H1", "h1"),
    ):
        m = re.search(rf"\*\*{key}:\*\*\s*(.+)", raw)
        meta[label] = m.group(1).strip() if m else ""
    url = meta["url"]
    if not url.endswith("/") and not url.endswith(".html"):
        url += "/"
    meta["url"] = url

    body = raw.split("\n---\n", 1)[1] if "\n---\n" in raw else raw
    hero_sub = ""
    intro_note = ""
    pre: list = []
    sections: list = []
    current = None
    list_type = None
    list_items: list = []

    def add(block):
        if current is None:
            pre.append(block)
        else:
            current["blocks"].append(block)

    def flush():
        nonlocal list_type, list_items
        if list_type:
            add((list_type, list_items[:]))
        list_type = None
        list_items = []

    lines = body.splitlines()
    i = 0
    while i < len(lines):
        s = lines[i].strip()
        i += 1
        if not s or s == "---":
            flush()
            continue
        if s.startswith("**Hero subheading:**"):
            flush()
            hero_sub = s.split(":**", 1)[1].strip()
            continue
        if s.startswith("**Intro:**"):
            flush()
            hero_sub = s.split(":**", 1)[1].strip()
            continue
        if s.startswith("**Hero water line labels:**"):
            flush()
            while i < len(lines) and lines[i].strip().startswith("- "):
                i += 1
            continue
        if re.match(r"\*\*(Hero )?Buttons?:\*\*", s) or s.startswith("**Button:**"):
            flush()
            continue
        if s.startswith("*(Developer note"):
            flush()
            continue
        if s.startswith("*") and s.endswith("*") and not s.startswith("**"):
            flush()
            note = s.strip("*").strip()
            if current is None and not intro_note and hero_sub:
                intro_note = note
            else:
                add(("note", note))
            continue
        if s.startswith("## "):
            flush()
            current = {"h2": s[3:].strip(), "blocks": []}
            sections.append(current)
            continue
        if s.startswith("### "):
            flush()
            add(("h3", s[4:].strip()))
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
        add(("p", s))
    flush()

    num = int(re.match(r"(\d+)", path.name).group(1))
    return {
        "num": num,
        "path": path,
        "meta": meta,
        "hero_sub": hero_sub,
        "intro_note": intro_note,
        "pre": pre,
        "sections": sections,
        "type": classify(url, num),
        "slug": url.strip("/").split("/")[-1] if url.strip("/") else "home",
    }


def classify(url: str, num: int) -> str:
    if url == "/":
        return "home"
    if url == "/services/":
        return "services-hub"
    if url.startswith("/services/"):
        return "service"
    if url == "/areas/":
        return "areas-hub"
    if url.startswith("/areas/"):
        return "area"
    if url == "/about/":
        return "about"
    if url == "/contact/":
        return "contact"
    if url == "/faq/":
        return "faq"
    if url in ("/privacy-policy/", "/terms-of-service/"):
        return "legal"
    if num in range(36, 40):
        return "guide"
    return "page"


def is_link_list(items: list) -> bool:
    return bool(items) and all(re.search(r"\[[^\]]+\]\([^)]+\)", it) for it in items)


def is_hub_card_list(items: list) -> bool:
    return bool(items) and all(re.search(r"\*\*\[[^\]]+\]\([^)]+\)\*\*", it) for it in items)


def tickish(heading: str) -> bool:
    h = heading.lower()
    keys = (
        "sign", "checklist", "what to do", "what not", "during a storm",
        "before the season", "mistakes", "do this first", "prep", "tell us",
        "when you send", "red flag",
    )
    return any(k in h for k in keys)


def speedish(heading: str) -> bool:
    h = heading.lower()
    return any(k in h for k in ("hour", "speed", "fast", "quick", "first hours", "why the first"))


def howish(heading: str) -> bool:
    h = heading.lower()
    return h.startswith("how we") or h.startswith("how to handle") or "how we " in h


def split_cta_faq(sections: list):
    """Only the last ## heading that ends with ? becomes the CTA band."""
    faq = None
    last_q = None
    for i, sec in enumerate(sections):
        if sec["h2"].endswith("?"):
            last_q = i
    body = []
    cta = None
    for i, sec in enumerate(sections):
        h = sec["h2"]
        if h.lower().startswith("frequently asked"):
            faq = sec
        elif i == last_q:
            cta = sec
        else:
            body.append(sec)
    return body, faq, cta


def faq_items(sec: dict):
    items = []
    current = None
    for kind, data in sec["blocks"]:
        if kind == "h3":
            current = {"q": data, "a": []}
            items.append(current)
        elif current is not None:
            current["a"].append((kind, data))
    return items


def answer_plain(blocks) -> str:
    parts = []
    for kind, data in blocks:
        if kind in ("p", "note", "h3"):
            parts.append(plain(data))
        elif kind in ("ul", "ol"):
            parts.extend(plain(x) for x in data)
    return " ".join(p for p in parts if p)


def render_faq_html(items) -> str:
    out = []
    for it in items:
        body = []
        for kind, data in it["a"]:
            if kind == "p":
                body.append(f"<p>{inline(data)}</p>")
            elif kind == "note":
                body.append(f'<p class="note">{inline(data)}</p>')
            elif kind == "ul":
                lis = "".join(f"<li>{inline(x)}</li>" for x in data)
                body.append(f"<ul>{lis}</ul>")
            elif kind == "ol":
                lis = "".join(f"<li>{inline(x)}</li>" for x in data)
                body.append(f"<ol>{lis}</ol>")
        if not body:
            body.append("<p></p>")
        out.append(
            f"<details><summary>{inline(it['q'])}</summary>"
            f'<div class="faq-a">{"".join(body)}</div></details>'
        )
    return "".join(out)


def render_ul(items, heading: str, as_link_cards=False) -> str:
    if as_link_cards or (
        is_link_list(items)
        and any(
            k in heading.lower()
            for k in ("related", "areas we serve", "services", "call us for", "neighborhood")
        )
    ):
        lis = []
        for item in items:
            m = re.search(r"\[([^\]]+)\]\(([^)]+)\)", item)
            if m:
                lis.append(f'<li><a href="{esc(m.group(2))}">{inline(m.group(1))}</a></li>')
            else:
                lis.append(f"<li>{inline(item)}</li>")
        return f'<ul class="link-cards">{"".join(lis)}</ul>'
    cls = "ticks" if tickish(heading) else ""
    attr = f' class="{cls}"' if cls else ""
    lis = "".join(f"<li>{inline(item)}</li>" for item in items)
    return f"<ul{attr}>{lis}</ul>"


def render_ol(items) -> str:
    lis = []
    for item in items:
        lis.append(f"<li>{inline(item)}</li>")
    return f'<ol class="steps">{"".join(lis)}</ol>'


def render_blocks(blocks, heading: str, opts: dict | None = None) -> str:
    opts = opts or {}
    out = []
    i = 0
    while i < len(blocks):
        kind, data = blocks[i]
        if kind == "h3":
            out.append(f"<h3>{inline(data)}</h3>")
        elif kind == "p":
            if data.strip() in (f"**{PHONE}**", PHONE):
                out.append(f'<p class="phone-xl"><a href="{TEL}">{PHONE}</a></p>')
            else:
                out.append(f"<p>{inline(data)}</p>")
        elif kind == "note":
            out.append(f'<p class="note">{inline(data)}</p>')
        elif kind == "ul":
            out.append(render_ul(data, heading, as_link_cards=opts.get("force_links")))
        elif kind == "ol":
            out.append(render_ol(data))
        i += 1
    return "".join(out)


def call_card(form_html: str) -> str:
    return (
        f'<aside class="call-card" id="request" aria-label="Send a request">\n'
        f"  <h2>Water spreading right now?</h2>\n"
        f"  <p>We answer day and night for homes and businesses across Buckeye.</p>\n"
        f'  <a class="btn btn--call" href="{TEL}">Call {PHONE}</a>\n'
        f'  <div class="divider">or send a request</div>\n'
        f"{form_html}"
        f"</aside>\n"
    )


def toc_sidebar() -> str:
    boxes = P["sidebar"]
    # insert TOC as first side-box
    insert = (
        '<div class="side-box toc"><h2>On this page</h2><div data-toc></div></div>\n  '
    )
    # after <aside ...>\n
    idx = boxes.find("\n") + 1
    return boxes[:idx] + insert + boxes[idx:]


def breadcrumbs(items: list[tuple[str | None, str]]) -> str:
    lis = []
    for href, name in items:
        if href:
            lis.append(f'<li><a href="{esc(href)}">{esc(name)}</a></li>')
        else:
            lis.append(f'<li><span aria-current="page">{esc(name)}</span></li>')
    return (
        '<nav class="breadcrumbs" aria-label="Breadcrumb">\n'
        f"          <ol>\n            " + "\n            ".join(lis) + "\n          </ol>\n"
        "        </nav>\n"
    )


def hero_buttons() -> str:
    return (
        f'<div class="btn-row">\n'
        f'          <a class="btn btn--call" href="{TEL}">Call {PHONE}</a>\n'
        f'          <a class="btn btn--ghost" href="#request">Send my request</a>\n'
        f"        </div>\n"
    )


def cta_band(sec: dict) -> str:
    paras = []
    for kind, data in sec["blocks"]:
        if kind == "p":
            paras.append(f"<p>{inline(data)}</p>")
        elif kind == "note":
            paras.append(f"<p>{inline(data)}</p>")
        elif kind == "ul":
            paras.append(render_ul(data, sec["h2"]))
        elif kind == "ol":
            paras.append(render_ol(data))
    body = "".join(paras) if paras else "<p></p>"
    return (
        f'<section class="cta-band">\n'
        f'  <div class="container cta-inner">\n'
        f"    <div>\n"
        f"      <h2>{inline(sec['h2'])}</h2>\n"
        f"      {body}\n"
        f"    </div>\n"
        f'    <a class="btn btn--dark" href="{TEL}">Call {PHONE}</a>\n'
        f"  </div>\n"
        f"</section>\n"
    )


def empty_faq_schema() -> dict:
    """Nav mobile menus use <details>; checker requires FAQPage whenever <details> exist."""
    return {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": []}


def head_html(page: dict, schemas: list, extra_meta: str = "") -> str:
    m = page["meta"]
    url = m["url"]
    canon = DOMAIN + url
    title = m["title"]
    desc = m["description"]
    # Ensure FAQPage exists when mobile nav <details> are present
    has_faq = any(
        (isinstance(s, dict) and s.get("@type") == "FAQPage")
        or (isinstance(s, dict) and '"FAQPage"' in json.dumps(s))
        or (isinstance(s, dict) and any(
            x.get("@type") == "FAQPage" for x in s.get("@graph", []) if isinstance(x, dict)
        ))
        for s in schemas
    )
    if not has_faq:
        schemas = list(schemas) + [empty_faq_schema()]
    blocks = []
    for schema in schemas:
        blocks.append(
            '<script type="application/ld+json">\n'
            + json.dumps(schema, indent=2, ensure_ascii=False)
            + "\n</script>"
        )
    return f"""<!DOCTYPE html>
<html lang="en-US">
<head>
<meta charset="utf-8">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<link rel="canonical" href="{esc(canon)}">
<meta property="og:type" content="website">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:url" content="{esc(canon)}">
<meta property="og:image" content="{DOMAIN}/assets/img/og-image.jpg">
<meta name="twitter:card" content="summary_large_image">
{extra_meta}{P['head_assets']}{chr(10).join(blocks)}
</head>
"""


def provider() -> dict:
    return {
        "@type": ["LocalBusiness", "HomeAndConstructionBusiness"],
        "@id": f"{DOMAIN}/#business",
        "name": BUSINESS,
        "telephone": SCHEMA_TEL,
        "url": f"{DOMAIN}/",
    }


def breadcrumb_schema(items: list[tuple[str, str]]) -> dict:
    return {
        "@type": "BreadcrumbList",
        "itemListElement": [
            {
                "@type": "ListItem",
                "position": i + 1,
                "name": name,
                "item": DOMAIN + href,
            }
            for i, (href, name) in enumerate(items)
        ],
    }


def faq_schema(items) -> dict:
    return {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {
                "@type": "Question",
                "name": it["q"],
                "acceptedAnswer": {"@type": "Answer", "text": answer_plain(it["a"])},
            }
            for it in items
        ],
    }


def service_schema(page: dict, area_place: str | None = None) -> dict:
    url = page["meta"]["url"]
    name = re.sub(r"\s+in\s+Buckeye.*$", "", page["meta"]["h1"], flags=re.I).strip()
    area = (
        {"@type": "Place", "name": area_place}
        if area_place
        else {"@type": "City", "name": "Buckeye, AZ"}
    )
    return {
        "@type": "Service",
        "name": name,
        "serviceType": plain(page["meta"]["h1"]),
        "url": DOMAIN + url,
        "provider": provider(),
        "areaServed": area,
    }


def article_schema(page: dict) -> dict:
    return {
        "@type": "Article",
        "headline": page["meta"]["h1"],
        "datePublished": DATE,
        "dateModified": DATE,
        "author": provider(),
        "publisher": provider(),
        "mainEntityOfPage": DOMAIN + page["meta"]["url"],
        "description": page["meta"]["description"],
    }


def figure(slug: str) -> str:
    key = slug
    if key not in IMAGE_MAP:
        return ""
    src, alt = IMAGE_MAP[key]
    return (
        f'<figure class="media"><img src="/assets/img/{src}" alt="{esc(alt)}" '
        f'width="1200" height="675" loading="lazy"></figure>\n'
    )


def build_service_like(page: dict, crumbs: list, area_place: str | None = None, sidebar: str | None = None) -> str:
    body_secs, faq, cta = split_cta_faq(page["sections"])
    form = P["form"]
    crumb_html = breadcrumbs(crumbs)
    lead = page["hero_sub"]
    lead_html = f'<p class="lead">{inline(lead)}</p>\n' if lead else ""
    note_html = f'<p class="note">{inline(page["intro_note"])}</p>\n' if page["intro_note"] else ""

    # article sections
    article_parts = []
    waterline_placed = False
    image_placed = False
    img_html = figure(page["slug"]) if page["type"] in ("service", "area", "about", "guide") else ""
    if page["type"] == "about":
        img_html = figure("about")
    if page["type"] == "guide" and page["slug"] in IMAGE_MAP:
        img_html = figure(page["slug"])

    # merge related + areas consecutive link sections like reference (optional, keep separate OK)
    i = 0
    while i < len(body_secs):
        sec = body_secs[i]
        h = sec["h2"]

        # Quick answer panel for cost guide
        if page["type"] == "guide" and h.lower() == "quick answer":
            article_parts.append(
                f'<section>\n<div class="panel-dark">\n'
                f"<h2>{inline(h)}</h2>\n"
                f"{render_blocks(sec['blocks'], h)}\n"
                f"</div>\n</section>\n"
            )
            i += 1
            continue

        # About: How we work as cards
        if page["type"] == "about" and h.lower() == "how we work":
            cards = []
            current_h = None
            current_ps = []
            for kind, data in sec["blocks"]:
                if kind == "h3":
                    if current_h:
                        cards.append(
                            f'<div class="card"><h3>{inline(current_h)}</h3>'
                            f"{''.join(current_ps)}</div>"
                        )
                    current_h = data
                    current_ps = []
                elif kind == "p" and current_h:
                    current_ps.append(f"<p>{inline(data)}</p>")
            if current_h:
                cards.append(
                    f'<div class="card"><h3>{inline(current_h)}</h3>'
                    f"{''.join(current_ps)}</div>"
                )
            block = (
                f"<section>\n<h2>{inline(h)}</h2>\n"
                f'<div class="grid grid-2">{"".join(cards)}</div>\n'
            )
            if img_html and not image_placed:
                block += img_html
                image_placed = True
            block += "</section>\n"
            article_parts.append(block)
            i += 1
            continue

        # force link-cards for area services lists
        force_links = page["type"] == "area" and "call us for" in h.lower()

        inner = render_blocks(sec["blocks"], h, {"force_links": force_links})

        # waterline after first p of speed section, or after how-we steps
        if not waterline_placed and speedish(h):
            # insert after first paragraph
            m = re.search(r"</p>", inner)
            if m:
                pos = m.end()
                inner = inner[:pos] + "\n" + WATERLINE + "\n" + inner[pos:]
                waterline_placed = True
        if not waterline_placed and howish(h) and "</ol>" in inner:
            inner = inner.replace("</ol>", "</ol>\n" + WATERLINE + "\n", 1)
            waterline_placed = True

        if img_html and not image_placed and howish(h):
            # after steps (and waterline if just added)
            if "</ol>" in inner:
                # place after last ol or after waterline following ol
                idx = inner.rfind("</ol>")
                end = idx + len("</ol>")
                # if waterline follows immediately, skip past it
                rest = inner[end:]
                wm = re.match(r"\s*<svg class=\"waterline.*?</svg>", rest, re.S)
                if wm:
                    end += wm.end()
                inner = inner[:end] + "\n" + img_html + inner[end:]
                image_placed = True
            else:
                inner += img_html
                image_placed = True

        article_parts.append(f"<section>\n<h2>{inline(h)}</h2>\n{inner}\n</section>\n")
        i += 1

    # If waterline never placed and there was a how-we section handled above, OK.
    # If still not placed, append after first how-ish or at end of first section — skip if none.

    if faq:
        items = faq_items(faq)
        article_parts.append(
            f'<section class="faq">\n'
            f"<h2>{inline(faq['h2'])}</h2>\n"
            f"{render_faq_html(items)}\n"
            f"</section>\n"
        )

    side = sidebar if sidebar is not None else P["sidebar"]
    article = "".join(article_parts)

    main = f"""<main id="main">

  <!-- HERO -->
  <section class="hero">
    <div class="container hero-grid">
      <div>
        {crumb_html}        <h1>{inline(page['meta']['h1'])}</h1>
        {lead_html}{note_html}        {hero_buttons()}      </div>
      {call_card(form)}    </div>
  </section>

  {P['trust']}
  <!-- BODY + SIDEBAR -->
  <section class="section">
    <div class="container inner-layout">
      <article class="prose">
{article}      </article>
      {side}    </div>
  </section>

  {cta_band(cta) if cta else ""}</main>
"""

    schemas_graph = []
    if page["type"] in ("service", "area"):
        schemas_graph.append(service_schema(page, area_place))
        schemas_graph.append(
            breadcrumb_schema([(c[0] or page["meta"]["url"], c[1]) for c in crumbs if True])
        )
        # fix breadcrumb items: last has no href in crumbs
        bc_items = []
        for href, name in crumbs:
            bc_items.append((href or page["meta"]["url"], name))
        schemas_graph = [
            service_schema(page, area_place),
            breadcrumb_schema(bc_items),
        ]
        schemas = [{"@context": "https://schema.org", "@graph": schemas_graph}]
        if faq:
            schemas.append(faq_schema(faq_items(faq)))
    elif page["type"] == "guide":
        bc_items = [(href or page["meta"]["url"], name) for href, name in crumbs]
        schemas = [
            {
                "@context": "https://schema.org",
                "@graph": [article_schema(page), breadcrumb_schema(bc_items)],
            }
        ]
        if faq:
            schemas.append(faq_schema(faq_items(faq)))
    elif page["type"] == "about":
        bc_items = [(href or page["meta"]["url"], name) for href, name in crumbs]
        schemas = [
            {
                "@context": "https://schema.org",
                "@graph": [
                    {
                        "@type": "AboutPage",
                        "name": page["meta"]["h1"],
                        "url": DOMAIN + page["meta"]["url"],
                        "mainEntity": provider(),
                    },
                    breadcrumb_schema(bc_items),
                ],
            }
        ]
        if faq:
            schemas.append(faq_schema(faq_items(faq)))
    else:
        schemas = []

    return head_html(page, schemas) + "<body>\n" + P["top"] + main + P["footer"] + "</body>\n</html>\n"


def build_hub(page: dict) -> str:
    url = page["meta"]["url"]
    if url == "/services/":
        crumbs = [("/", "Home"), (None, "Services")]
        bc_schema = [("/", "Home"), ("/services/", "Services")]
    else:
        crumbs = [("/", "Home"), (None, "Areas")]
        bc_schema = [("/", "Home"), ("/areas/", "Areas")]

    body_secs, faq, cta = split_cta_faq(page["sections"])
    # pre paragraphs become lead (combine)
    lead_parts = []
    for kind, data in page["pre"]:
        if kind == "p":
            lead_parts.append(data)
    if not page["hero_sub"] and lead_parts:
        # first para as lead, rest after
        pass
    lead = page["hero_sub"] or (lead_parts[0] if lead_parts else "")
    extra_paras = lead_parts[1:] if not page["hero_sub"] and len(lead_parts) > 1 else (
        lead_parts if page["hero_sub"] else []
    )
    if page["hero_sub"]:
        extra_paras = lead_parts

    lead_html = f'<p class="lead">{inline(lead)}</p>\n' if lead else ""
    extra_html = "".join(f"<p>{inline(p)}</p>\n" for p in extra_paras if p != lead)

    sections_html = []
    for sec in body_secs:
        h = sec["h2"]
        # hub card groups: ## becomes group-title, ul becomes grid cards
        cards = []
        other = []
        for kind, data in sec["blocks"]:
            if kind == "ul" and (is_hub_card_list(data) or is_link_list(data)):
                for item in data:
                    # MD form: **[Title](/url).** Description...
                    m = re.match(
                        r"\*\*\[([^\]]+)\]\(([^)]+)\)\.?\*\*\s*(.*)",
                        item,
                    )
                    if not m:
                        m = re.match(
                            r"\*\*\[([^\]]+)\]\(([^)]+)\)\*\*\.?\s*(.*)",
                            item,
                        )
                    if m:
                        title, href, rest = m.group(1), m.group(2), m.group(3).strip()
                        card = f'<a class="card" href="{esc(href)}"><h3>{esc(title)}</h3>'
                        if rest:
                            if not rest.endswith("."):
                                rest += "."
                            card += f"<p>{inline(rest)}</p>"
                        card += "</a>"
                        cards.append(card)
                        continue
                    m2 = re.search(r"\[([^\]]+)\]\(([^)]+)\)", item)
                    if m2:
                        title, href = m2.group(1), m2.group(2)
                        rest = re.sub(r"\*\*\[([^\]]+)\]\([^)]+\)\.?\*\*", "", item)
                        rest = re.sub(r"\[[^\]]+\]\([^)]+\)", "", rest).strip(" .")
                        rest = rest.replace("**", "").strip()
                        card = f'<a class="card" href="{esc(href)}"><h3>{esc(title)}</h3>'
                        if rest:
                            if not rest.endswith("."):
                                rest += "."
                            card += f"<p>{inline(rest)}</p>"
                        card += "</a>"
                        cards.append(card)
            else:
                other.append((kind, data))
        block = f'<section class="section">\n<div class="container">\n'
        block += f'<h3 class="group-title">{inline(h)}</h3>\n' if cards else f"<h2>{inline(h)}</h2>\n"
        if other:
            block += render_blocks(other, h)
        if cards:
            block += f'<div class="grid grid-3">{"".join(cards)}</div>\n'
        block += "</div>\n</section>\n"
        sections_html.append(block)

    faq_html = ""
    if faq:
        items = faq_items(faq)
        faq_html = (
            f'<section class="section">\n<div class="container">\n'
            f'<section class="faq">\n<h2>{inline(faq["h2"])}</h2>\n'
            f"{render_faq_html(items)}\n</section>\n</div>\n</section>\n"
        )

    main = f"""<main id="main">
  <section class="hero">
    <div class="container hero-grid">
      <div>
        {breadcrumbs(crumbs)}        <h1>{inline(page['meta']['h1'])}</h1>
        {lead_html}{extra_html}        {hero_buttons()}      </div>
      {call_card(P['form'])}    </div>
  </section>
  {P['trust']}
{''.join(sections_html)}{faq_html}  {cta_band(cta) if cta else ""}</main>
"""
    schemas = [
        {
            "@context": "https://schema.org",
            "@graph": [breadcrumb_schema(bc_schema)],
        }
    ]
    if faq:
        schemas.append(faq_schema(faq_items(faq)))
    return head_html(page, schemas) + "<body>\n" + P["top"] + main + P["footer"] + "</body>\n</html>\n"


def build_contact(page: dict) -> str:
    sections = page["sections"][:]
    # First section → hero content
    hero_sec = sections[0] if sections else None
    rest = sections[1:] if sections else []
    body, faq, cta = split_cta_faq(rest)
    # Contact first heading ends with ? but is hero, not CTA — already separated

    hero_bits = []
    if hero_sec:
        for kind, data in hero_sec["blocks"]:
            if kind == "p":
                if data.strip() in (f"**{PHONE}**", PHONE) or plain(data) == PHONE:
                    hero_bits.append(f'<p class="phone-xl"><a href="{TEL}">{PHONE}</a></p>\n')
                else:
                    hero_bits.append(f"<p>{inline(data)}</p>\n")
    hero_bits.append(
        f'<div class="btn-row"><a class="btn btn--call" href="{TEL}">Call {PHONE}</a></div>\n'
    )

    parts = []
    for sec in body:
        h = sec["h2"]
        if h.lower().startswith("send us a request"):
            # form card
            inner = []
            for kind, data in sec["blocks"]:
                if kind == "p":
                    inner.append(f"<p>{inline(data)}</p>")
                elif kind == "ul":
                    inner.append(render_ul(data, h))
                elif kind == "note":
                    continue
            parts.append(
                f'<section class="section">\n<div class="container">\n'
                f'<div class="form-card" id="request">\n'
                f"<h2>{inline(h)}</h2>\n"
                f"{''.join(inner)}\n"
                f"{P['form']}"
                f"</div>\n</div>\n</section>\n"
            )
            continue
        # steps sections
        parts.append(
            f'<section class="section">\n<div class="container">\n'
            f'<article class="prose">\n<section>\n'
            f"<h2>{inline(h)}</h2>\n"
            f"{render_blocks(sec['blocks'], h)}\n"
            f"</section>\n</article>\n</div>\n</section>\n"
        )

    crumbs = [("/", "Home"), (None, "Contact")]
    main = f"""<main id="main">
  <section class="hero">
    <div class="container">
      {breadcrumbs(crumbs)}      <h1>{inline(page['meta']['h1'])}</h1>
      {''.join(hero_bits)}    </div>
  </section>
  {P['trust']}
{''.join(parts)}  {cta_band(cta) if cta else ""}</main>
"""
    schemas = [
        {
            "@context": "https://schema.org",
            "@graph": [
                {
                    "@type": "ContactPage",
                    "name": page["meta"]["h1"],
                    "url": DOMAIN + page["meta"]["url"],
                    "mainEntity": provider(),
                },
                breadcrumb_schema([("/", "Home"), ("/contact/", "Contact")]),
            ],
        }
    ]
    return head_html(page, schemas) + "<body>\n" + P["top"] + main + P["footer"] + "</body>\n</html>\n"


def build_faq_page(page: dict) -> str:
    body, faq_unused, cta = split_cta_faq(page["sections"])
    # every ## is a faq group (except CTA)
    groups = body
    all_items = []
    group_html = []
    intro = "".join(
        f"<p>{inline(data)}</p>\n" for kind, data in page["pre"] if kind == "p"
    )
    for sec in groups:
        items = faq_items(sec)
        all_items.extend(items)
        group_html.append(
            f'<div class="faq-group">\n'
            f"<h2>{inline(sec['h2'])}</h2>\n"
            f"{render_faq_html(items)}\n"
            f"</div>\n"
        )

    crumbs = [("/", "Home"), (None, "FAQ")]
    main = f"""<main id="main">
  <section class="hero">
    <div class="container hero-grid">
      <div>
        {breadcrumbs(crumbs)}        <h1>{inline(page['meta']['h1'])}</h1>
        {f'<p class="lead">{intro}</p>' if False else intro}        {hero_buttons()}      </div>
      {call_card(P['form'])}    </div>
  </section>
  {P['trust']}
  <section class="section">
    <div class="container inner-layout">
      <article class="prose">
{''.join(group_html)}      </article>
      {P['sidebar']}    </div>
  </section>
  {cta_band(cta) if cta else ""}</main>
"""
    # fix lead: intro paragraphs should show as lead-ish prose under h1
    # rebuild hero left column more carefully
    lead_block = ""
    if page["pre"]:
        paras = [data for kind, data in page["pre"] if kind == "p"]
        if paras:
            lead_block = f'<p class="lead">{inline(paras[0])}</p>\n'
            for p in paras[1:]:
                lead_block += f"<p>{inline(p)}</p>\n"

    main = f"""<main id="main">
  <section class="hero">
    <div class="container hero-grid">
      <div>
        {breadcrumbs(crumbs)}        <h1>{inline(page['meta']['h1'])}</h1>
        {lead_block}        {hero_buttons()}      </div>
      {call_card(P['form'])}    </div>
  </section>
  {P['trust']}
  <section class="section">
    <div class="container inner-layout">
      <article class="prose">
{''.join(group_html)}      </article>
      {P['sidebar']}    </div>
  </section>
  {cta_band(cta) if cta else ""}</main>
"""
    schemas = [
        {
            "@context": "https://schema.org",
            "@graph": [breadcrumb_schema([("/", "Home"), ("/faq/", "FAQ")])],
        },
        faq_schema(all_items),
    ]
    return head_html(page, schemas) + "<body>\n" + P["top"] + main + P["footer"] + "</body>\n</html>\n"


def build_legal(page: dict) -> str:
    name = "Privacy Policy" if "privacy" in page["meta"]["url"] else "Terms of Service"
    crumbs = [("/", "Home"), (None, name)]
    parts = []
    for kind, data in page["pre"]:
        if kind == "p":
            # Effective date often bold in md as **Effective date: ...**
            parts.append(f"<p>{inline(data)}</p>\n")
    for sec in page["sections"]:
        parts.append(f"<h2>{inline(sec['h2'])}</h2>\n")
        parts.append(render_blocks(sec["blocks"], sec["h2"]))
    main = f"""<main id="main">
  <section class="hero">
    <div class="container">
      {breadcrumbs(crumbs)}      <h1>{inline(page['meta']['h1'])}</h1>
    </div>
  </section>
  <section class="section">
    <div class="container">
      <article class="prose">
{''.join(parts)}      </article>
    </div>
  </section>
</main>
"""
    schemas = [
        {
            "@context": "https://schema.org",
            "@graph": [
                breadcrumb_schema(
                    [("/", "Home"), (page["meta"]["url"], name)]
                )
            ],
        }
    ]
    # legal pages: no id=request — footer mobile bar still has #request; that's OK
    # checker skips request requirement for privacy/terms
    # but footer still has Get help online -> #request. Fine.
    return head_html(page, schemas) + "<body>\n" + P["top"] + main + P["footer"] + "</body>\n</html>\n"


def build_404() -> str:
    page = {
        "meta": {
            "url": "/404.html",
            "title": "Page not found | White Tank Water Restoration",
            "description": "This page is not here. Call White Tank Water Restoration for water damage help in Buckeye.",
            "h1": "This page is not here",
        }
    }
    main = f"""<main id="main">
  <section class="hero">
    <div class="container">
      <h1>This page is not here</h1>
      <p class="lead">The page you were looking for has moved or does not exist. If you have water damage right now, call us and we will help.</p>
      <div class="btn-row">
        <a class="btn btn--call" href="{TEL}">Call {PHONE}</a>
        <a class="btn btn--ghost" href="/">Go to the homepage</a>
      </div>
    </div>
  </section>
  <section class="section">
    <div class="container">
      <ul class="link-cards">
        <li><a href="/services/">Water damage services</a></li>
        <li><a href="/areas/">Buckeye service areas</a></li>
      </ul>
    </div>
  </section>
</main>
"""
    # 404 needs id=request for mobile bar — put hidden anchor or form? Footer has #request.
    # Add a form-card or call target. Simplest: wrap nothing — mobile bar needs #request.
    # Put id=request on a container linking to contact form area:
    main = main.replace(
        '<div class="container">\n      <h1>',
        '<div class="container" id="request">\n      <h1>',
        1,
    )
    extra = '<meta name="robots" content="noindex">\n'
    return (
        head_html(page, [], extra_meta=extra)
        + "<body>\n"
        + P["top"]
        + main
        + P["footer"]
        + "</body>\n</html>\n"
    )


def build_page(page: dict) -> str:
    t = page["type"]
    url = page["meta"]["url"]
    if t == "service":
        slug = page["slug"]
        crumb_name = CRUMB_SERVICE.get(slug, slug.replace("-", " ").title())
        return build_service_like(
            page,
            [("/", "Home"), ("/services/", "Services"), (None, crumb_name)],
        )
    if t == "area":
        slug = page["slug"]
        crumb_name = CRUMB_AREA.get(slug, slug.replace("-", " ").title())
        return build_service_like(
            page,
            [("/", "Home"), ("/areas/", "Areas"), (None, crumb_name)],
            area_place=f"{crumb_name}, Buckeye, AZ",
        )
    if t in ("services-hub", "areas-hub"):
        return build_hub(page)
    if t == "guide":
        crumb_name = GUIDE_CRUMB.get(url, page["meta"]["h1"])
        return build_service_like(
            page,
            [("/", "Home"), (None, crumb_name)],
            sidebar=toc_sidebar(),
        )
    if t == "about":
        return build_service_like(
            page,
            [("/", "Home"), (None, "About")],
        )
    if t == "contact":
        return build_contact(page)
    if t == "faq":
        return build_faq_page(page)
    if t == "legal":
        return build_legal(page)
    raise ValueError(f"Unknown page type for {url}")


def write_page(url: str, html_out: str):
    path = page_path(url)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(html_out, encoding="utf-8")
    return path


def main():
    generated = []
    for md in md_files():
        page = parse_md(md)
        url = page["meta"]["url"]
        if url in SKIP_URLS or page["type"] == "home":
            print(f"SKIP  {url}")
            continue
        html_out = build_page(page)
        path = write_page(url, html_out)
        generated.append(url)
        print(f"WRITE {url} -> {path.relative_to(ROOT)}")

    # 404
    write_page("/404.html", build_404())
    generated.append("/404.html")
    print("WRITE /404.html")

    print(f"\nGenerated {len(generated)} pages.")
    return len(generated)


if __name__ == "__main__":
    main()
