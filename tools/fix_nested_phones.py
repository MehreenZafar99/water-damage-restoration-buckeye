#!/usr/bin/env python3
"""Fix nested phone buttons created by over-eager phone replacement."""
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


def clean_button(classes: str) -> str:
    classes = classes.strip()
    # Prefer outer intent: header-cta / block / dark over inline
    if "header-cta" in classes:
        cls = "btn btn--call header-cta"
    elif "btn--block" in classes:
        cls = "btn btn--call btn--block"
    elif "btn--dark" in classes:
        cls = "btn btn--dark"
        return f'<a class="{cls}" href="tel:+16235550148">{ICON} {PHONE}</a>'
    elif "btn--call-inline" in classes and "btn--block" not in classes and "header-cta" not in classes:
        # keep inline only if it was truly inline-only
        cls = "btn btn--call btn--call-inline"
    else:
        cls = "btn btn--call"
        if "btn--call-inline" in classes and "header-cta" not in classes and "btn--block" not in classes:
            # outer had both? prefer non-inline full button
            cls = "btn btn--call"
    return f'<a class="{cls}" href="tel:+16235550148">{ICON} {PHONE}</a>'


NESTED = re.compile(
    r'<a class="(btn[^"]*)" href="tel:\+16235550148">'
    r'(?:(?!</a>).)*?'
    r'<a class="btn[^"]*" href="tel:\+16235550148">.*?</a>\s*'
    r'</a>',
    re.S,
)


def fix_html(html: str) -> str:
    prev = None
    while prev != html:
        prev = html
        html = NESTED.sub(lambda m: clean_button(m.group(1)), html)
    return html


def main():
    n = 0
    for p in ROOT.rglob("*.html"):
        if "files" in p.parts or "content" in p.parts:
            continue
        original = p.read_text(encoding="utf-8")
        html = fix_html(original)
        if html != original:
            p.write_text(html, encoding="utf-8", newline="\n")
            n += 1
    print(f"Fixed {n} files")

    # verify no nested left
    bad = []
    for p in ROOT.rglob("*.html"):
        if "files" in p.parts:
            continue
        t = p.read_text(encoding="utf-8")
        if re.search(r'btn--call[^>]*>[\s\S]{0,400}<a class="btn', t):
            bad.append(str(p))
    print("remaining nested", len(bad))
    for b in bad[:5]:
        print(" ", b)


if __name__ == "__main__":
    main()
