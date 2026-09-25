# Generates the static site from the markdown copy. Not used at runtime.
import html
import json
import os
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DOMAIN = "https://waterdamagerestorationbuckeyeaz.com"
PHONE = "(623) 555-0148"
TEL = "tel:+16235550148"

SERVICES = [
    ("Emergency water removal", "/services/emergency-water-removal/"),
    ("Flood damage cleanup", "/services/flood-damage-cleanup/"),
    ("Burst pipe cleanup", "/services/burst-pipe-cleanup/"),
    ("Slab leak water damage", "/services/slab-leak-water-damage/"),
    ("Water heater leak cleanup", "/services/water-heater-leak-cleanup/"),
    ("AC leak water damage", "/services/ac-leak-water-damage/"),
    ("Ceiling and roof leak damage", "/services/ceiling-roof-leak-damage/"),
    ("Washer, dishwasher and fridge leaks", "/services/appliance-leak-cleanup/"),
    ("Toilet overflow cleanup", "/services/toilet-overflow-cleanup/"),
    ("Sewage backup cleanup", "/services/sewage-backup-cleanup/"),
    ("Structural drying", "/services/structural-drying/"),
    ("Wet carpet and floors", "/services/carpet-floor-water-damage/"),
    ("Mold remediation", "/services/mold-remediation/"),
    ("Storm damage restoration", "/services/storm-damage-restoration/"),
    ("New construction water damage", "/services/new-construction-water-damage/"),
    ("Commercial water damage", "/services/commercial-water-damage/"),
]

AREAS = [
    ("Verrado", "/areas/verrado/"),
    ("Sundance", "/areas/sundance/"),
    ("Tartesso", "/areas/tartesso/"),
    ("Festival Ranch", "/areas/festival-ranch/"),
    ("Sun City Festival", "/areas/sun-city-festival/"),
    ("Westpark", "/areas/westpark/"),
    ("Blue Horizons", "/areas/blue-horizons/"),
    ("Historic Downtown Buckeye", "/areas/downtown-buckeye/"),
    ("Teravalis", "/areas/teravalis/"),
    ("Riata West", "/areas/riata-west/"),
    ("Watson Estates", "/areas/watson-estates/"),
    ("Sienna Hills", "/areas/sienna-hills/"),
    ("Valencia", "/areas/valencia/"),
    ("Trillium", "/areas/trillium/"),
]

GUIDES = [
    ("Water damage cost", "/water-damage-cost-buckeye/"),
    ("Insurance claim guide", "/insurance-claim-guide/"),
    ("First 24 hours", "/first-24-hours-after-water-damage/"),
    ("Monsoon water damage", "/monsoon-water-damage-guide/"),
    ("FAQ", "/faq/"),
]

CRUMBS = {
    "/about/": "About",
    "/contact/": "Contact",
    "/faq/": "FAQ",
    "/privacy-policy/": "Privacy policy",
    "/terms-of-service/": "Terms of service",
    "/water-damage-cost-buckeye/": "Water damage cost",
    "/insurance-claim-guide/": "Insurance claim guide",
    "/first-24-hours-after-water-damage/": "First 24 hours",
    "/monsoon-water-damage-guide/": "Monsoon water damage",
}

PHOTOS = {
    "/": [("hero-water-extraction.webp", "Water extraction equipment removing standing water from a tile floor in a Buckeye home", False)],
    "/services/emergency-water-removal/": [("hero-water-extraction.webp", "Emergency extraction of standing water inside a Buckeye home", True)],
    "/services/flood-damage-cleanup/": [
        ("flooded-living-room.webp", "Living room in a Buckeye home with floodwater across the floor", True),
        ("monsoon-storm-buckeye.webp", "Monsoon storm over Buckeye with heavy rain that can push water indoors", True),
    ],
    "/services/slab-leak-water-damage/": [("slab-leak-floor.webp", "Tile floor in a Buckeye home showing signs of water from under the slab", True)],
    "/services/water-heater-leak-cleanup/": [("water-heater-leak.webp", "Water heater leak spreading across a Buckeye garage floor", True)],
    "/services/ac-leak-water-damage/": [("ceiling-water-stain.webp", "Ceiling stain in a Buckeye home from an air conditioner leak", True)],
    "/services/ceiling-roof-leak-damage/": [("ceiling-water-stain.webp", "Water stain and drip on a Buckeye ceiling after a roof leak", True)],
    "/services/appliance-leak-cleanup/": [("wet-carpet.webp", "Wet carpet beside an appliance leak in a Buckeye home", True)],
    "/services/carpet-floor-water-damage/": [
        ("wet-carpet.webp", "Wet carpet pulled back for drying in a Buckeye home", True),
        ("slab-leak-floor.webp", "Flooring opened to dry a wet slab in a Buckeye home", True),
    ],
    "/services/structural-drying/": [("drying-equipment.webp", "Air movers and a dehumidifier drying walls and floors in a Buckeye home", True)],
    "/services/mold-remediation/": [("mold-wall.webp", "Mold on drywall after water damage inside a Buckeye home", True)],
    "/services/storm-damage-restoration/": [("flooded-living-room.webp", "Buckeye living room soaked after wind and rain from a storm", True)],
    "/services/commercial-water-damage/": [("commercial-building-water.webp", "Water on the floor of a Buckeye commercial building", True)],
    "/about/": [("drying-equipment.webp", "Drying equipment set up inside a Buckeye home", True)],
    "/monsoon-water-damage-guide/": [("monsoon-storm-buckeye.webp", "Summer monsoon clouds and rain over Buckeye", True)],
}

FILES = [
    "01-homepage.md", "02-services-hub.md", "03-emergency-water-removal.md",
    "04-flood-damage-cleanup.md", "05-burst-pipe-cleanup.md", "06-slab-leak-water-damage.md",
    "07-water-heater-leak-cleanup.md", "08-ac-leak-water-damage.md", "09-ceiling-roof-leak-damage.md",
    "10-appliance-leak-cleanup.md", "11-toilet-overflow-cleanup.md", "12-sewage-backup-cleanup.md",
    "13-structural-drying.md", "14-carpet-floor-water-damage.md", "15-mold-remediation.md",
    "16-storm-damage-restoration.md", "17-new-construction-water-damage.md",
    "18-commercial-water-damage.md", "19-areas-hub.md", "20-about.md", "21-contact.md",
    "22-area-verrado.md", "23-area-sundance.md", "24-area-tartesso.md", "25-area-festival-ranch.md",
    "26-area-sun-city-festival.md", "27-area-westpark.md", "28-area-blue-horizons.md",
    "29-area-downtown-buckeye.md", "30-area-teravalis.md", "31-area-riata-west.md",
    "32-area-watson-estates.md", "33-area-sienna-hills.md", "34-area-valencia.md",
    "35-area-trillium.md", "36-water-damage-cost-buckeye.md", "37-insurance-claim-guide.md",
    "38-first-24-hours-after-water-damage.md", "39-monsoon-water-damage-guide.md",
    "40-faq.md", "41-privacy-policy.md", "42-terms-of-service.md",
]


def locate(name):
    for path in (
        ROOT / name,
        ROOT / "content" / "batch-1" / name,
        ROOT / "content" / "batch-2" / name,
    ):
        if path.exists():
            return path
    raise FileNotFoundError(name)


def esc(text):
    return html.escape(text, quote=True)


def inline(text):
    safe = esc(text)
    safe = re.sub(
        r"\[([^\]]+)\]\(([^)]+)\)",
        lambda m: f'<a href="{m.group(2)}">{m.group(1)}</a>',
        safe,
    )
    safe = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", safe)
    safe = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"<em>\1</em>", safe)
    safe = safe.replace(PHONE, f'<a href="{TEL}">{PHONE}</a>')
    return safe


def plain(text):
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    text = text.replace("**", "").replace("*", "")
    return re.sub(r"\s+", " ", text).strip()


def slug(text):
    value = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return value or "section"


def service_url(name):
    key = name.strip().rstrip(".").lower()
    for label, url in SERVICES:
        if label.lower() == key:
            return url
    return None


def page_type(url, num):
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


def parse(path, num):
    lines = path.read_text(encoding="utf-8").splitlines()
    meta = {}
    body_start = 0
    for i, line in enumerate(lines):
        if line.strip() == "---":
            body_start = i + 1
            break
        match = re.match(r"\*\*(URL|Title tag|Meta description|H1):\*\*\s*(.*)", line.strip())
        if match:
            meta[{"URL": "url", "Title tag": "title", "Meta description": "description", "H1": "h1"}[match.group(1)]] = match.group(2).strip()
    hero = {"sub": "", "buttons": [], "labels": []}
    pre = []
    sections = []
    current = None
    list_type = None
    list_items = []

    def add(block):
        if current is None:
            pre.append(block)
        else:
            current["blocks"].append(block)

    def flush():
        nonlocal list_type, list_items
        if list_type:
            add((list_type, list_items))
        list_type = None
        list_items = []

    i = body_start
    while i < len(lines):
        line = lines[i].strip()
        i += 1
        if not line or line == "---":
            flush()
            continue
        if line.startswith("**Hero subheading:**"):
            flush()
            hero["sub"] = line.split(":**", 1)[1].strip()
            continue
        if line.startswith("**Hero water line labels:**"):
            flush()
            labels = []
            while i < len(lines) and lines[i].strip().startswith("- "):
                labels.append(lines[i].strip()[2:].strip())
                i += 1
            hero["labels"] = labels
            continue
        if re.match(r"\*\*Hero buttons:\*\*|\*\*Buttons:\*\*|\*\*Button:\*\*", line):
            flush()
            labels = [part.strip() for part in line.split(":**", 1)[1].split("|")]
            if current is None:
                hero["buttons"] = labels
            else:
                add(("buttons", labels))
            continue
        if line.startswith("**Intro:**"):
            flush()
            add(("intro", line.split(":**", 1)[1].strip()))
            continue
        if line.startswith("*(Developer note:"):
            flush()
            add(("devnote", line))
            continue
        if line.startswith("*") and line.endswith("*") and not line.startswith("**"):
            flush()
            add(("note", line.strip("*").strip()))
            continue
        if line.startswith("## "):
            flush()
            current = {"h2": line[3:].strip(), "blocks": []}
            sections.append(current)
            continue
        if line.startswith("### "):
            flush()
            add(("h3", line[4:].strip()))
            continue
        numbered = re.match(r"\d+\.\s+(.*)", line)
        if numbered:
            if list_type not in (None, "ol"):
                flush()
            list_type = "ol"
            list_items.append(numbered.group(1).strip())
            continue
        if line.startswith("- "):
            if list_type not in (None, "ul"):
                flush()
            list_type = "ul"
            list_items.append(line[2:].strip())
            continue
        flush()
        add(("p", line))
    flush()
    url = meta["url"] if meta["url"].endswith("/") else meta["url"] + "/"
    return {
        "url": url,
        "title": meta["title"],
        "description": meta["description"],
        "h1": meta["h1"],
        "hero": hero,
        "pre": pre,
        "sections": sections,
        "type": page_type(url, num),
        "num": num,
        "source": path.name,
    }


def buttons_html(labels):
    parts = []
    for label in labels:
        if label.startswith("Call ") or label == PHONE:
            parts.append(f'<a class="btn btn-saffron btn-call" href="{TEL}">{esc(label)}</a>')
    if not parts:
        return ""
    return f'<div class="btn-row">{"".join(parts)}</div>'


def call_button():
    return f'<div class="btn-row"><a class="btn btn-saffron btn-call" href="{TEL}">Call {PHONE}</a></div>'


def is_link_list(items):
    return bool(items) and all(re.search(r"\[[^\]]+\]\([^)]+\)", item) for item in items)


def tick_heading(text):
    hay = text.lower()
    keys = ("checklist", "what to do", "what not", "during a storm", "before the season", "mistakes to avoid", "do this first", "prep")
    return any(key in hay for key in keys)


def speed_heading(text):
    hay = text.lower()
    return any(key in hay for key in ("hour", "speed", "fast", "quick"))


def render_ul(items, ticks=False, large=False, small=False):
    if large or small:
        cls = "card-grid tiles-lg" if large else "card-grid compact"
        cards = []
        for item in items:
            match = re.match(r"\*\*([^*]+)\*\*\s*(.*)", item)
            if match:
                name = match.group(1).strip()
                rest = match.group(2).strip()
                url = service_url(name)
                body = f"<strong>{esc(name)}</strong>"
                if rest:
                    body += f"<p>{inline(rest)}</p>"
                tile_cls = "tile tile-lg" if large else "tile"
                if url:
                    cards.append(f'<a class="{tile_cls}" href="{url}">{body}</a>')
                else:
                    cards.append(f'<div class="{tile_cls}">{body}</div>')
            else:
                url = service_url(item)
                label = inline(item)
                if url:
                    cards.append(f'<a class="tile" href="{url}">{label}</a>')
                else:
                    cards.append(f'<div class="tile">{label}</div>')
        return f'<div class="{cls}">{"".join(cards)}</div>'
    if is_link_list(items):
        cards = []
        for item in items:
            match = re.search(r"\[[^\]]+\]\(([^)]+)\)", item)
            href = match.group(1)
            text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", item)
            cards.append(f'<a class="link-card" href="{esc(href)}">{inline(text)}</a>')
        return f'<div class="card-grid">{"".join(cards)}</div>'
    tag_cls = "ticks" if ticks else "plain"
    lis = "".join(f"<li>{inline(item)}</li>" for item in items)
    return f'<ul class="{tag_cls}">{lis}</ul>'


def render_ol(items, horizontal=False, ticks=False):
    if horizontal:
        lis = "".join(f"<li>{inline(item)}</li>" for item in items)
        return f'<ol class="steps-row">{lis}</ol>'
    lis = "".join(f"<li>{inline(item)}</li>" for item in items)
    return f'<ol class="steps">{lis}</ol>'


def render_blocks(blocks, heading, page, mode=None):
    ticks = tick_heading(heading)
    out = []
    tile_mode = None
    i = 0
    while i < len(blocks):
        kind, data = blocks[i]
        if kind == "devnote":
            i += 1
            continue
        if kind == "h3":
            out.append(f"<h3>{inline(data)}</h3>")
            if page["type"] == "home":
                low = data.lower()
                if "large tile" in low:
                    tile_mode = "large"
                elif "smaller" in low:
                    tile_mode = "small"
            i += 1
            continue
        if kind == "ul":
            large = tile_mode == "large"
            small = tile_mode == "small"
            out.append(render_ul(data, ticks=ticks, large=large, small=small))
            tile_mode = None
            i += 1
            continue
        if kind == "ol":
            horizontal = page["url"] == "/" and heading.startswith("How we restore")
            out.append(render_ol(data, horizontal=horizontal))
            i += 1
            continue
        if kind == "p":
            if " · " in data and any(name in data for name, _url in AREAS):
                names = [part.strip() for part in data.split("·")]
                cards = []
                for name in names:
                    url = dict(AREAS).get(name)
                    if url:
                        cards.append(f'<a class="tile" href="{url}">{esc(name)}</a>')
                    else:
                        cards.append(f'<div class="tile">{esc(name)}</div>')
                out.append(f'<div class="area-grid">{"".join(cards)}</div>')
            elif data.strip() in (f"**{PHONE}**", PHONE):
                out.append(f'<p class="phone-xl"><a href="{TEL}">{PHONE}</a></p>')
            else:
                out.append(f"<p>{inline(data)}</p>")
            i += 1
            continue
        if kind == "intro":
            out.append(f'<p class="lead">{inline(data)}</p>')
            i += 1
            continue
        if kind == "note":
            out.append(f'<p class="note">{inline(data)}</p>')
            i += 1
            continue
        if kind == "buttons":
            out.append(buttons_html(data))
            i += 1
            continue
        i += 1
    return "".join(out)


def two_column(blocks, heading, page):
    intro = []
    groups = []
    current = None
    for block in blocks:
        if block[0] == "h3":
            current = {"h": block[1], "blocks": []}
            groups.append(current)
        elif current:
            current["blocks"].append(block)
        else:
            intro.append(block)
    if len(groups) < 2:
        return None
    html_intro = render_blocks(intro, heading, page)
    articles = []
    for group in groups:
        articles.append(f'<article><h3>{inline(group["h"])}</h3>{render_blocks(group["blocks"], group["h"], page)}</article>')
    return html_intro + f'<div class="two-col">{"".join(articles)}</div>'


def faq_parts(blocks):
    intro = []
    items = []
    current = None
    for block in blocks:
        if block[0] == "h3":
            current = {"q": block[1], "a": []}
            items.append(current)
        elif current:
            current["a"].append(block)
        else:
            intro.append(block)
    return intro, items


def answer_text(blocks):
    parts = []
    for kind, data in blocks:
        if kind in ("p", "intro", "note", "h3"):
            parts.append(plain(data))
        elif kind in ("ul", "ol"):
            parts.extend(plain(item) for item in data)
    return " ".join(part for part in parts if part)


def render_faq_items(items):
    chunks = []
    for item in items:
        body = render_blocks(item["a"], item["q"], {"type": "faq", "url": ""})
        chunks.append(f'<details class="faq"><summary>{inline(item["q"])}</summary>{body}</details>')
    return "".join(chunks)


def form_html():
    return f'''<div class="form-card" id="request">
      <h2>Request help</h2>
      <form id="lead-form" method="post" action="{esc("https://FORM_ENDPOINT_PLACEHOLDER")}" novalidate>
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
      </form>
    </div>'''


def water_svg(animated=False, labels=None):
    klass = "waterline"
    fill = 'class="water-fill"' if animated else ""
    texts = ""
    if labels:
        for label, y in zip(labels, (250, 204, 158)):
            texts += f'<text x="210" y="{y}" fill="#2A2326" font-size="13" font-family="Atkinson Hyperlegible, sans-serif">{esc(label)}</text>'
    width = 640 if labels else 280
    return f'''<svg class="{klass}" viewBox="0 0 {width} 320" role="img" aria-label="Cross section of a wall, baseboard and floor with a rising water line">
      <rect x="36" y="28" width="128" height="230" fill="#FFFFFF" stroke="#8C6A75" stroke-width="3"/>
      <rect x="36" y="214" width="128" height="44" fill="#ECE8E6" stroke="#8C6A75" stroke-width="3"/>
      <rect x="20" y="258" width="160" height="28" fill="#5B1E2D"/>
      <rect x="39" y="150" width="122" height="105" fill="#8C6A75" fill-opacity="0.35" {fill}/>
      <line x1="164" y1="150" x2="200" y2="150" stroke="#8C6A75" stroke-width="3"/>
      <line x1="164" y1="196" x2="200" y2="196" stroke="#8C6A75" stroke-width="3"/>
      <line x1="164" y1="242" x2="200" y2="242" stroke="#8C6A75" stroke-width="3"/>
      {texts}
    </svg>'''


def photos_html(page):
    figures = []
    for filename, alt, lazy in PHOTOS.get(page["url"], []):
        loading = "lazy" if lazy else "eager"
        figures.append(
            f'<figure class="photo"><img src="/assets/img/{filename}" alt="{esc(alt)}" width="1200" height="800" loading="{loading}" onerror="this.parentElement.classList.add(\'img-missing\'); this.remove();"></figure>'
        )
    return "".join(figures)


def nav_html(current):
    def mark(url):
        return ' aria-current="page"' if url == current else ""

    service_links = "".join(f'<a href="{url}"{mark(url)}>{esc(label)}</a>' for label, url in SERVICES)
    area_links = "".join(f'<a href="{url}"{mark(url)}>{esc(label)}</a>' for label, url in AREAS)
    cost = f'<a href="/water-damage-cost-buckeye/"{mark("/water-damage-cost-buckeye/")}>Cost</a>'
    about = f'<a href="/about/"{mark("/about/")}>About</a>'
    contact = f'<a href="/contact/"{mark("/contact/")}>Contact</a>'
    return f'''<nav class="site-nav" id="site-nav" aria-label="Primary">
        <div class="nav-drop">
          <button type="button" aria-expanded="false" aria-controls="menu-services" aria-haspopup="true">Services</button>
          <div class="dropdown" id="menu-services">{service_links}</div>
        </div>
        <div class="nav-drop">
          <button type="button" aria-expanded="false" aria-controls="menu-areas" aria-haspopup="true">Areas</button>
          <div class="dropdown" id="menu-areas">{area_links}</div>
        </div>
        {cost}
        {about}
        {contact}
      </nav>'''


def header_html(page):
    return f'''  <a class="skip" href="#main">Skip to content</a>
  <header class="site-header">
    <div class="wrap header-inner">
      <a class="logo" href="/">
        <svg width="40" height="28" viewBox="0 0 40 28" aria-hidden="true"><path fill="#5B1E2D" d="M0 26 L8 14 L14 20 L22 6 L30 16 L40 10 L40 26 Z"/></svg>
        <span>White Tank Water Restoration</span>
      </a>
      <button class="nav-toggle" id="nav-toggle" type="button" aria-expanded="false" aria-controls="site-nav">Menu</button>
      {nav_html(page["url"])}
      <a class="btn btn-saffron header-call" href="{TEL}">Call {PHONE}</a>
    </div>
  </header>'''


def footer_html():
    services = "".join(f'<li><a href="{url}">{esc(label)}</a></li>' for label, url in SERVICES)
    areas = "".join(f'<li><a href="{url}">{esc(label)}</a></li>' for label, url in AREAS)
    guides = "".join(f'<li><a href="{url}">{esc(label)}</a></li>' for label, url in GUIDES)
    return f'''<footer class="site-footer">
    <div class="wrap">
      <p class="footer-lead">White Tank Water Restoration helps Buckeye homes and businesses recover from water damage, day or night.</p>
      <div class="footer-grid">
        <div><h2>Services</h2><ul>{services}</ul></div>
        <div><h2>Areas</h2><ul>{areas}</ul></div>
        <div><h2>Guides</h2><ul>{guides}</ul></div>
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
  </div>'''


def crumbs_html(page):
    if page["url"] == "/":
        return ""
    items = [("Home", "/")]
    if page["url"] == "/services/":
        items.append(("Services", None))
    elif page["url"].startswith("/services/"):
        items.append(("Services", "/services/"))
        label = dict((url, name) for name, url in SERVICES)[page["url"]]
        items.append((label, None))
    elif page["url"] == "/areas/":
        items.append(("Areas", None))
    elif page["url"].startswith("/areas/"):
        items.append(("Areas", "/areas/"))
        label = dict((url, name) for name, url in AREAS)[page["url"]]
        items.append((label, None))
    else:
        items.append((CRUMBS.get(page["url"], page["h1"]), None))
    lis = []
    for name, url in items:
        if url:
            lis.append(f'<li><a href="{url}">{esc(name)}</a></li>')
        else:
            lis.append(f"<li>{esc(name)}</li>")
    page["crumbs"] = items
    return f'<nav class="crumbs" aria-label="Breadcrumb"><div class="wrap"><ol>{"".join(lis)}</ol></div></nav>'


def schema(page, faqs):
    graph = []
    business = {
        "@type": ["LocalBusiness", "HomeAndConstructionBusiness"],
        "@id": DOMAIN + "/#business",
        "name": "White Tank Water Restoration",
        "url": DOMAIN + "/",
        "telephone": PHONE,
        "openingHours": "Mo-Su 00:00-23:59",
        "address": {
            "@type": "PostalAddress",
            "addressLocality": "Buckeye",
            "addressRegion": "AZ",
            "postalCode": "85326",
            "addressCountry": "US",
        },
        "geo": {"@type": "GeoCoordinates", "latitude": 33.3703, "longitude": -112.5838},
        "areaServed": {"@type": "City", "name": "Buckeye", "address": {"@type": "PostalAddress", "addressLocality": "Buckeye", "addressRegion": "AZ", "addressCountry": "US"}},
    }
    if page["type"] == "home":
        graph.append(business)
        graph.append({"@type": "WebSite", "@id": DOMAIN + "/#website", "name": "White Tank Water Restoration", "url": DOMAIN + "/"})
    if page["type"] == "service":
        graph.append({
            "@type": "Service",
            "name": page["h1"],
            "serviceType": page["h1"],
            "url": DOMAIN + page["url"],
            "provider": {"@id": DOMAIN + "/#business"},
            "areaServed": {"@type": "City", "name": "Buckeye", "address": {"@type": "PostalAddress", "addressLocality": "Buckeye", "addressRegion": "AZ", "addressCountry": "US"}},
        })
    if page["type"] == "area":
        place = dict((url, name) for name, url in AREAS)[page["url"]]
        graph.append({
            "@type": "Service",
            "name": page["h1"],
            "serviceType": "Water damage restoration",
            "url": DOMAIN + page["url"],
            "provider": {"@id": DOMAIN + "/#business"},
            "areaServed": {"@type": "Place", "name": f"{place}, Buckeye, AZ"},
        })
    if page["type"] == "guide":
        graph.append({
            "@type": "Article",
            "headline": page["h1"],
            "datePublished": "2026-09-25",
            "dateModified": "2026-09-25",
            "mainEntityOfPage": DOMAIN + page["url"],
            "author": {"@type": "Organization", "name": "White Tank Water Restoration", "url": DOMAIN + "/"},
            "publisher": {"@type": "Organization", "name": "White Tank Water Restoration", "url": DOMAIN + "/"},
        })
    if faqs:
        graph.append({
            "@type": "FAQPage",
            "mainEntity": [
                {"@type": "Question", "name": item["q"], "acceptedAnswer": {"@type": "Answer", "text": item["text"]}}
                for item in faqs
            ],
        })
    crumbs = page.get("crumbs")
    if crumbs:
        graph.append({
            "@type": "BreadcrumbList",
            "itemListElement": [
                {"@type": "ListItem", "position": index + 1, "name": name, "item": DOMAIN + (url or page["url"])}
                for index, (name, url) in enumerate(crumbs)
            ],
        })
    if not graph:
        return ""
    payload = json.dumps({"@context": "https://schema.org", "@graph": graph}, ensure_ascii=False).replace("<", "\\u003c")
    return f'<script type="application/ld+json">{payload}</script>'


def head(page, faqs, robots=""):
    canon = DOMAIN + page["url"]
    image = DOMAIN + "/assets/img/og-image.jpg"
    robot = f'\n  <meta name="robots" content="{robots}">' if robots else ""
    return f'''<!DOCTYPE html>
<html lang="en-US">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{esc(page["title"])}</title>
  <meta name="description" content="{esc(page["description"])}">
  <link rel="canonical" href="{canon}">{robot}
  <meta property="og:type" content="{'article' if page['type']=='guide' else 'website'}">
  <meta property="og:title" content="{esc(page["title"])}">
  <meta property="og:description" content="{esc(page["description"])}">
  <meta property="og:url" content="{canon}">
  <meta property="og:image" content="{image}">
  <meta property="og:image:width" content="1200">
  <meta property="og:image:height" content="630">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="{esc(page["title"])}">
  <meta name="twitter:description" content="{esc(page["description"])}">
  <meta name="twitter:image" content="{image}">
  <link rel="icon" href="/favicon.svg" type="image/svg+xml">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Source+Sans+3:wght@400;600;700&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="/assets/css/styles.css">
  <!-- analytics -->
  {schema(page, faqs)}
</head>'''


def wants_form(page):
    return page["type"] in ("home", "service", "area", "guide", "contact")


def form_in_hero(page):
    return page["type"] in ("home", "service")


def render_section(page, section, faqs, speed_used):
    heading = section["h2"]
    is_faq = heading.lower() == "frequently asked questions" or (page["type"] == "faq" and not heading.endswith("?"))
    if is_faq:
        intro, items = faq_parts(section["blocks"])
        for item in items:
            faqs.append({"q": plain(item["q"]), "text": answer_text(item["a"])})
        body = render_blocks(intro, heading, page) + render_faq_items(items)
        return f'<section class="section"><div class="wrap"><h2 id="{slug(heading)}">{inline(heading)}</h2>{body}</div></section>', speed_used
    if page["url"] == "/" and heading.startswith("Water damage services"):
        body = render_blocks(section["blocks"], heading, page)
        return f'<section class="section"><div class="wrap"><h2 id="{slug(heading)}">{inline(heading)}</h2>{body}</div></section>', speed_used
    if (page["url"] == "/" and heading.startswith("Why water damage")) or (page["type"] == "about" and heading == "How we work"):
        body = two_column(section["blocks"], heading, page)
        if body is None:
            body = render_blocks(section["blocks"], heading, page)
        return f'<section class="section"><div class="wrap"><h2 id="{slug(heading)}">{inline(heading)}</h2>{body}</div></section>', speed_used
    body = render_blocks(section["blocks"], heading, page)
    panel = "do this first" in heading.lower()
    inner = f'<div class="panel">{body}</div>' if panel else body
    return f'<section class="section"><div class="wrap"><h2 id="{slug(heading)}">{inline(heading)}</h2>{inner}</div></section>', speed_used


def render_page(page):
    faqs = []
    crumbs = crumbs_html(page)
    pre_html = render_blocks(page["pre"], "", page)
    hero_buttons = ""
    if page["hero"]["buttons"]:
        hero_buttons = buttons_html(page["hero"]["buttons"])
    elif page["type"] in ("service", "area"):
        hero_buttons = call_button()
    sub = f'<p class="lead">{inline(page["hero"]["sub"])}</p>' if page["hero"]["sub"] else ""
    if page["type"] in ("home", "service", "area") and not hero_buttons:
        hero_buttons = call_button()
    hero_inner = f'<div class="hero-copy"><h1>{esc(page["h1"])}</h1>{sub}{hero_buttons}</div>'
    if page["type"] not in ("home", "service"):
        hero_inner = f'<div class="hero-copy"><h1>{esc(page["h1"])}</h1>{sub}{pre_html}{hero_buttons}</div>'
        pre_html = ""
    sections_html = []
    normal_index = 0
    speed_used = False
    last = page["sections"][-1] if page["sections"] else None
    for section in page["sections"]:
        if section["h2"].lower().startswith("send us a request"):
            continue
        if section is last and section["h2"].rstrip().endswith("?"):
            body = render_blocks(section["blocks"], section["h2"], page)
            if "btn-call" not in body:
                body += call_button()
            sections_html.append(("cta", f'<section class="cta"><div class="wrap"><h2>{inline(section["h2"])}</h2>{body}</div></section>'))
            continue
        html_section, speed_used = render_section(page, section, faqs, speed_used)
        if 'class="section"' in html_section:
            klass = "section alt" if normal_index % 2 else "section"
            html_section = html_section.replace('class="section"', f'class="{klass}"', 1)
            normal_index += 1
        sections_html.append(("section", html_section))
    body_sections = [chunk for _kind, chunk in sections_html]
    joined = "".join(body_sections)
    if page["type"] == "guide":
        toc_items = []
        for section in page["sections"]:
            toc_items.append(f'<li><a href="#{slug(section["h2"])}">{esc(section["h2"])}</a></li>')
        joined = f'''<div class="wrap guide-layout">
        <nav class="toc" aria-label="On this page"><ol>{"".join(toc_items)}</ol></nav>
        <div>{pre_html}{joined}</div>
      </div>'''
        pre_html = ""
    elif pre_html:
        joined = f'<section class="section"><div class="wrap">{pre_html}</div></section>' + joined
    print_class = " print-guide" if page["url"] == "/first-24-hours-after-water-damage/" else ""
    doc = f'''{head(page, faqs)}
<body class="{page["type"]}{print_class}">
  {header_html(page)}
  {crumbs}
  <main id="main">
    <header class="hero"><div class="wrap">{hero_inner}</div></header>
    {joined}
  </main>
  {footer_html()}
  <script src="/assets/js/main.js" defer></script>
</body>
</html>
'''
    return doc


def render_404():
    page = {
        "url": "/404.html",
        "title": "Page not found | White Tank Water Restoration",
        "description": "This page is not here. Call White Tank Water Restoration for water damage help in Buckeye.",
        "h1": "This page is not here",
        "type": "page",
        "crumbs": [],
    }
    # canonical not useful; still build a simple head with noindex
    page["url"] = "/404.html"
    content = f'''{head(page, [], robots="noindex")}
<body>
  {header_html(page)}
  <main id="main">
    <header class="hero"><div class="wrap hero-copy">
      <h1>This page is not here</h1>
      <p class="lead">The page you were looking for has moved or does not exist. If you have water damage right now, call us and we will help.</p>
      <div class="btn-row">
        <a class="btn btn-saffron" href="{TEL}">Call {PHONE}</a>
        <a class="btn btn-oxblood" href="/">Go to the homepage</a>
      </div>
      <p><a href="/services/">Water damage services</a></p>
      <p><a href="/areas/">Buckeye service areas</a></p>
    </div></header>
  </main>
  {footer_html()}
  <script src="/assets/js/main.js" defer></script>
</body>
</html>
'''
    return content


def write_pages(pages):
    for page in pages:
        target = ROOT / "index.html" if page["url"] == "/" else ROOT / page["url"].strip("/") / "index.html"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(render_page(page), encoding="utf-8")
    (ROOT / "404.html").write_text(render_404(), encoding="utf-8")


def write_meta(pages):
    urls = [DOMAIN + page["url"] for page in pages]
    body = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for url in urls:
        body.append(f"  <url><loc>{url}</loc><lastmod>2026-09-25</lastmod></url>")
    body.append("</urlset>\n")
    (ROOT / "sitemap.xml").write_text("\n".join(body), encoding="utf-8")
    (ROOT / "robots.txt").write_text(
        "User-agent: *\nAllow: /\nDisallow: /content/\n\nSitemap: https://waterdamagerestorationbuckeyeaz.com/sitemap.xml\n",
        encoding="utf-8",
    )
    (ROOT / "_headers").write_text(
        """/assets/*
  Cache-Control: public, max-age=31536000, immutable

/*
  X-Content-Type-Options: nosniff
  Referrer-Policy: strict-origin-when-cross-origin
  X-Frame-Options: SAMEORIGIN

/content/*
  X-Robots-Tag: noindex
""",
        encoding="utf-8",
    )


def move_content():
    (ROOT / "content" / "batch-1").mkdir(parents=True, exist_ok=True)
    (ROOT / "content" / "batch-2").mkdir(parents=True, exist_ok=True)
    for name in FILES:
        src = locate(name)
        num = int(name[:2])
        dest_dir = ROOT / "content" / ("batch-1" if num <= 21 else "batch-2")
        dest = dest_dir / name
        if src.resolve() != dest.resolve():
            shutil.move(str(src), str(dest))


def make_images():
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        import subprocess
        subprocess.check_call(["python", "-m", "pip", "install", "pillow"])
        from PIL import Image, ImageDraw, ImageFont
    folder = ROOT / "assets" / "img"
    folder.mkdir(parents=True, exist_ok=True)
    stone = (236, 232, 230)
    ox = (91, 30, 45)
    dusk = (140, 106, 117)
    paper = (255, 255, 255)
    ink = (42, 35, 38)
    saffron = (242, 169, 0)

    def canvas():
        image = Image.new("RGB", (1200, 800), stone)
        return image, ImageDraw.Draw(image)

    specs = {
        "hero-water-extraction.webp": "extract",
        "flooded-living-room.webp": "flood",
        "slab-leak-floor.webp": "slab",
        "water-heater-leak.webp": "heater",
        "ceiling-water-stain.webp": "ceiling",
        "drying-equipment.webp": "dry",
        "monsoon-storm-buckeye.webp": "storm",
        "wet-carpet.webp": "carpet",
        "mold-wall.webp": "mold",
        "commercial-building-water.webp": "commercial",
    }
    for filename, kind in specs.items():
        image, draw = canvas()
        draw.rectangle((80, 80, 1120, 720), fill=paper, outline=dusk, width=6)
        if kind == "extract":
            draw.rectangle((80, 520, 1120, 720), fill=dusk)
            draw.rectangle((180, 360, 420, 560), fill=ox)
        elif kind == "flood":
            draw.rectangle((80, 430, 1120, 720), fill=dusk)
            draw.rectangle((200, 250, 480, 460), fill=ox)
            draw.rectangle((620, 300, 980, 470), fill=stone, outline=ox, width=4)
        elif kind == "slab":
            for x in range(120, 1100, 80):
                draw.line((x, 140, x, 680), fill=dusk, width=3)
            for y in range(140, 700, 80):
                draw.line((100, y, 1100, y), fill=dusk, width=3)
            draw.ellipse((420, 300, 820, 560), fill=dusk)
        elif kind == "heater":
            draw.rounded_rectangle((460, 180, 740, 620), radius=40, fill=ox)
            draw.rectangle((140, 600, 1060, 700), fill=dusk)
        elif kind == "ceiling":
            draw.rectangle((80, 80, 1120, 220), fill=paper, outline=dusk, width=4)
            draw.ellipse((430, 110, 790, 250), fill=dusk)
            draw.polygon([(600, 220), (560, 520), (640, 520)], fill=dusk)
        elif kind == "dry":
            draw.rectangle((160, 280, 360, 640), fill=ox)
            draw.rectangle((460, 360, 760, 640), fill=dusk)
            draw.rectangle((840, 300, 1040, 640), fill=ox)
            draw.rectangle((500, 180, 720, 280), fill=saffron)
        elif kind == "storm":
            draw.polygon([(0, 520), (180, 300), (340, 460), (520, 180), (760, 420), (980, 240), (1200, 480), (1200, 800), (0, 800)], fill=ox)
            for x in range(80, 1100, 40):
                draw.line((x, 40, x - 80, 260), fill=dusk, width=4)
        elif kind == "carpet":
            for y in range(160, 700, 36):
                draw.rectangle((100, y, 1100, y + 18), fill=dusk if (y // 36) % 2 == 0 else ox)
        elif kind == "mold":
            draw.rectangle((200, 120, 1000, 680), fill=paper, outline=ox, width=8)
            for point in ((300, 200), (480, 260), (700, 180), (820, 340), (400, 420), (640, 500), (860, 480), (520, 560)):
                draw.ellipse((point[0], point[1], point[0] + 70, point[1] + 48), fill=dusk)
        elif kind == "commercial":
            draw.rectangle((180, 160, 1020, 680), outline=ox, width=10)
            for x in (260, 460, 660, 860):
                draw.rectangle((x, 240, x + 120, 360), fill=dusk)
                draw.rectangle((x, 420, x + 120, 540), fill=stone, outline=ox, width=3)
            draw.rectangle((80, 620, 1120, 720), fill=dusk)
        image.save(folder / filename, "WEBP", quality=80)
    og = Image.new("RGB", (1200, 630), ox)
    draw = ImageDraw.Draw(og)
    draw.polygon([(40, 430), (180, 250), (300, 380), (460, 140), (680, 360), (860, 200), (1160, 420), (1160, 520), (40, 520)], fill=dusk)
    draw.rectangle((0, 520, 1200, 630), fill=saffron)
    try:
        font = ImageFont.truetype("arial.ttf", 64)
        small = ImageFont.truetype("arial.ttf", 32)
    except OSError:
        font = ImageFont.load_default()
        small = font
    draw.text((60, 60), "White Tank Water Restoration", fill=paper, font=font)
    draw.text((60, 150), "Buckeye, AZ", fill=saffron, font=small)
    og.save(folder / "og-image.jpg", "JPEG", quality=86)


def visible_text(doc):
    doc = re.sub(r"<script[\s\S]*?</script>", " ", doc)
    doc = re.sub(r"<style[\s\S]*?</style>", " ", doc)
    doc = re.sub(r"<[^>]+>", " ", doc)
    doc = html.unescape(doc)
    return re.sub(r"\s+", " ", doc)


def line_words(line):
    line = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", line)
    line = line.replace("**", " ").replace("*", " ")
    line = line.replace("·", " ")
    return re.sub(r"\s+", " ", line).strip()


def verify(pages):
    problems = []
    css = (ROOT / "assets" / "css" / "styles.css").read_text(encoding="utf-8").lower()
    js = (ROOT / "assets" / "js" / "main.js").read_text(encoding="utf-8").lower()
    for token in ("teal", "navy", "green", "blue", "mint"):
        if re.search(r"\b" + token + r"\b", css):
            problems.append(f"color token {token} in css")
    html_paths = {page["url"]: (ROOT / "index.html" if page["url"] == "/" else ROOT / page["url"].strip("/") / "index.html") for page in pages}
    for page in pages:
        doc = html_paths[page["url"]].read_text(encoding="utf-8")
        if doc.count("<h1") != 1:
            problems.append(f'{page["url"]} h1 count {doc.count("<h1")}')
        if f'<title>{esc(page["title"])}</title>' not in doc:
            problems.append(f'{page["url"]} title mismatch')
        if f'content="{esc(page["description"])}"' not in doc:
            problems.append(f'{page["url"]} description mismatch')
        if f'href="{DOMAIN}{page["url"]}"' not in doc:
            problems.append(f'{page["url"]} canonical missing')
        for match in re.finditer(r'<script type="application/ld\+json">(.*?)</script>', doc):
            try:
                json.loads(match.group(1))
            except json.JSONDecodeError as error:
                problems.append(f'{page["url"]} schema {error}')
        text = visible_text(doc)
        source = locate(page["source"]).read_text(encoding="utf-8")
        body = source.split("---", 1)[1]
        for raw in body.splitlines():
            line = raw.strip()
            if not line or line == "---" or line.startswith("*(Developer note:") or line.startswith("**Hero water"):
                continue
            if line.startswith("**Hero ") or line.startswith("**Intro:**") or line.startswith("**Buttons:**") or line.startswith("**Button:**"):
                line = line.split(":**", 1)[1]
            line = re.sub(r"^#{1,3}\s*", "", line)
            line = re.sub(r"^\d+\.\s+", "", line)
            line = re.sub(r"^-\s+", "", line)
            cleaned = line_words(line)
            if cleaned and cleaned not in text:
                problems.append(f'{page["url"]} missing: {cleaned[:140]}')
        for href in re.findall(r'href="(/[^"]*)"', doc):
            if href.startswith("/assets") or href.startswith("/favicon"):
                continue
            path = href.split("#")[0]
            if path in ("/", ""):
                continue
            file_path = ROOT / path.strip("/") / "index.html"
            if not file_path.exists():
                problems.append(f'{page["url"]} bad link {href}')
    if not (ROOT / "404.html").exists():
        problems.append("404 missing")
    return problems


def main():
    pages = []
    for name in FILES:
        pages.append(parse(locate(name), int(name[:2])))
    write_pages(pages)
    write_meta(pages)
    move_content()
    make_images()
    problems = verify(pages)
    print(f"pages={len(pages)} problems={len(problems)}")
    for problem in problems[:80]:
        print(problem)


if __name__ == "__main__":
    main()
