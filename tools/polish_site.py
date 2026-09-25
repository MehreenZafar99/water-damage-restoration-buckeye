#!/usr/bin/env python3
"""Sitewide polish: phone→buttons, address/email in footers, content bounds helpers."""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]

ICON = (
    '<svg viewBox="0 0 24 24" aria-hidden="true">'
    '<path fill="currentColor" d="M6.6 10.8a15.1 15.1 0 0 0 6.6 6.6l2.2-2.2a1 1 0 0 1 1-.25'
    'c1.1.37 2.3.57 3.6.57a1 1 0 0 1 1 1V20a1 1 0 0 1-1 1A17 17 0 0 1 3 4a1 1 0 0 1 1-1'
    'h3.5a1 1 0 0 1 1 1c0 1.25.2 2.45.57 3.57a1 1 0 0 1-.25 1z"/></svg>'
)
PHONE = "(623) 555-0148"
BTN = f'<a class="btn btn--call btn--call-inline" href="tel:+16235550148">{ICON} {PHONE}</a>'
BTN_BLOCK = f'<a class="btn btn--call btn--block" href="tel:+16235550148">{ICON} {PHONE}</a>'

ADDRESS = "21430 W Yuma Rd, Suite 120, Buckeye, AZ 85326"
EMAIL = "contact@waterdamagerestorationbuckeyeaz.com"
EMAIL_LINK = f'<a href="mailto:{EMAIL}">{EMAIL}</a>'

FOOTER_CONTACT = f'''        <div class="footer-contact">
          {BTN}
          <p class="footer-meta">{EMAIL_LINK}<br>{ADDRESS}<br>Open 24 hours, 7 days a week<br>Serving Buckeye, AZ 85326 and 85396</p>
        </div>'''

FOOTER_OLD = re.compile(
    r'<p><a class="footer-phone"[^>]*>\(623\) 555-0148</a><br>Open 24 hours, 7 days a week<br>Serving Buckeye, AZ 85326 and 85396</p>',
)


def html_files():
    for p in ROOT.rglob("*.html"):
        if "files" in p.parts or "content" in p.parts:
            continue
        yield p


def protect_regions(html: str):
    """Hide head + JSON-LD from phone rewrites."""
    parts = []
    pattern = re.compile(
        r"(<head\b[^>]*>.*?</head>)|(<script\b[^>]*type=[\"']application/ld\+json[\"'][^>]*>.*?</script>)",
        re.I | re.S,
    )
    last = 0
    for m in pattern.finditer(html):
        parts.append(("body", html[last:m.start()]))
        parts.append(("skip", m.group(0)))
        last = m.end()
    parts.append(("body", html[last:]))
    return parts


def phone_to_buttons(chunk: str) -> str:
    # Skip if already a btn--call containing the number nearby — replace plain tel links first
    chunk = re.sub(
        r'<a href="tel:\+16235550148"(?! class="btn)[^>]*>\s*(?:Call\s+)?\(623\) 555-0148\s*</a>',
        BTN,
        chunk,
    )
    chunk = re.sub(
        r'<a class="footer-phone" href="tel:\+16235550148">\(623\) 555-0148</a>',
        BTN,
        chunk,
    )
    # Emergency bar: turn the linked number into a compact button
    chunk = re.sub(
        r'(Water in your home or business right now\? Call )'
        r'<a href="tel:\+16235550148">\(623\) 555-0148</a>'
        r'(, we answer day and night\.)',
        rf'\1{BTN}\2',
        chunk,
    )
    # Also if already rewritten partially
    chunk = re.sub(
        r'(Water in your home or business right now\? Call )'
        r'<a class="btn btn--call[^"]*" href="tel:\+16235550148">.*?</a>'
        r'(, we answer day and night\.)',
        rf'\1{BTN}\2',
        chunk,
        flags=re.S,
    )

    # Plain text phone not already inside an <a ...>
    def plain_phone(m):
        before = m.string[max(0, m.start() - 80) : m.start()]
        if re.search(r"<a\b[^>]*$", before):
            return m.group(0)
        if "btn--call" in before[-80:]:
            return m.group(0)
        return BTN

    chunk = re.sub(r"\(623\) 555-0148", plain_phone, chunk)
    return chunk


def update_footer(html: str) -> str:
    html = FOOTER_OLD.sub(FOOTER_CONTACT, html)
    # If footer already has button but missing address/email
    if EMAIL not in html and "footer-brand" in html:
        html = re.sub(
            r'(<div class="footer-brand">.*?</p>)\s*(?:<div class="footer-contact">.*?</div>|<p>.*?</p>)?',
            rf"\1\n{FOOTER_CONTACT}",
            html,
            count=1,
            flags=re.S,
        )
    return html


def process(path: Path) -> bool:
    original = path.read_text(encoding="utf-8")
    parts = protect_regions(original)
    out = []
    for kind, chunk in parts:
        if kind == "skip":
            out.append(chunk)
        else:
            out.append(phone_to_buttons(chunk))
    html = "".join(out)
    html = update_footer(html)
    if html != original:
        path.write_text(html, encoding="utf-8", newline="\n")
        return True
    return False


def main():
    n = sum(1 for p in html_files() if process(p))
    print(f"Updated {n} files")


if __name__ == "__main__":
    main()
