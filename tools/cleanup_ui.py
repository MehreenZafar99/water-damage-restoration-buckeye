#!/usr/bin/env python3
"""Safe UI cleanup: remove forms, waterlines, simplify call buttons. Never use DOTALL across page bodies."""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]

ICON = (
    '<svg viewBox="0 0 24 24" aria-hidden="true">'
    '<path fill="currentColor" d="M6.6 10.8a15.1 15.1 0 0 0 6.6 6.6l2.2-2.2a1 1 0 0 1 1-.25'
    'c1.1.37 2.3.57 3.6.57a1 1 0 0 1 1 1V20a1 1 0 0 1-1 1A17 17 0 0 1 3 4a1 1 0 0 1 1-1'
    'h3.5a1 1 0 0 1 1 1c0 1.25.2 2.45.57 3.57a1 1 0 0 1-.25 1z"/></svg>'
)

def phone_btn(extra_class=""):
    cls = "btn btn--call" + ((" " + extra_class) if extra_class else "")
    return f'<a class="{cls}" href="tel:+16235550148">{ICON} (623) 555-0148</a>'

CALL_CARD = f'''      <aside class="call-card" aria-label="Get help now">
        <h2>Need help now?</h2>
        <p>We answer day and night for homes and businesses across Buckeye.</p>
        {phone_btn()}
      </aside>'''

MOBILE = f'''<div class="mobile-bar">
  {phone_btn("btn--block")}
</div>'''


def html_files():
    out = []
    for p in ROOT.rglob("*.html"):
        if "files" in p.parts or "content" in p.parts:
            continue
        out.append(p)
    return out


def remove_forms(html: str) -> str:
    # Only remove form elements (non-greedy, form can't nest)
    return re.sub(r"<form\b[^>]*>.*?</form>", "", html, flags=re.I | re.S)


def remove_waterlines(html: str) -> str:
    return re.sub(
        r"<svg\b[^>]*class=\"[^\"]*waterline[^\"]*\"[^>]*>.*?</svg>",
        "",
        html,
        flags=re.I | re.S,
    )


def remove_form_ctas(html: str) -> str:
    # Ghost / request buttons — no DOTALL needed; these are single-line or short
    html = re.sub(
        r'\s*<a class="btn btn--ghost"[^>]*href="#request"[^>]*>[^<]*</a>',
        "",
        html,
    )
    html = re.sub(
        r'\s*<a class="btn[^"]*"[^>]*>\s*Send my request\s*</a>',
        "",
        html,
    )
    html = re.sub(r'\s*<div class="divider">or send a request</div>', "", html)
    html = re.sub(r' href="#request"', ' href="tel:+16235550148"', html)
    return html


def replace_call_cards(html: str) -> str:
    """Replace each call-card aside by finding matching open/close tags (no nested aside)."""
    out = []
    i = 0
    while True:
        start = html.find('<aside class="call-card"', i)
        if start < 0:
            out.append(html[i:])
            break
        out.append(html[i:start])
        end = html.find("</aside>", start)
        if end < 0:
            out.append(html[start:])
            break
        end += len("</aside>")
        out.append(CALL_CARD)
        i = end
    return "".join(out)


def replace_mobile_bar(html: str) -> str:
    return re.sub(r'<div class="mobile-bar">.*?</div>', MOBILE, html, flags=re.S)


def replace_tel_buttons(html: str) -> str:
    """Replace tel call buttons without DOTALL spanning the page."""
    # Pattern: opening a tag with btn--call and tel href, then content until </a>
    # Content may include SVG but must not include newlines spanning huge gaps —
    # allow whitespace/newlines only for short button innards (cap with {0,400})
    pattern = re.compile(
        r'<a class="(btn btn--call[^"]*)" href="tel:\+16235550148">(.{0,500}?)</a>',
        re.S,
    )

    def repl(m):
        classes = m.group(1)
        if "header-cta" in classes:
            return phone_btn("header-cta")
        if "btn--block" in classes:
            return phone_btn("btn--block")
        return phone_btn()

    return pattern.sub(repl, html)


def strip_call_word_in_dark_cta(html: str) -> str:
    # CTA band dark buttons: "Call (623)..." -> icon + number
    return re.sub(
        r'(<a class="btn btn--dark" href="tel:\+16235550148">)\s*Call \(623\) 555-0148\s*(</a>)',
        rf'\1{ICON} (623) 555-0148\2',
        html,
    )


def fix_homepage(html: str, path: Path) -> str:
    if path.resolve() != (ROOT / "index.html").resolve():
        return html

    # Why Buckeye cards
    m = re.search(
        r'(<h2>Why water damage in Buckeye is different</h2>.*?<div class="grid grid-2">)(.*?)(</div>\s*</div>\s*</section>)',
        html,
        flags=re.S,
    )
    if m:
        inner = re.sub(
            r"<div>\s*<h3>(.*?)</h3>\s*<p>(.*?)</p>\s*</div>",
            r'<div class="card topic-card"><h3>\1</h3><p>\2</p></div>',
            m.group(2),
            flags=re.S,
        )
        html = html[: m.start()] + m.group(1) + inner + m.group(3) + html[m.end() :]

    html = html.replace(
        '<div class="container grid grid-2">\n      <div>\n        <h2>We work with your insurance company</h2>',
        '<div class="container grid grid-2">\n      <div class="info-panel">\n        <h2>We work with your insurance company</h2>',
    )
    html = html.replace("Emergency help (large tiles)", "Emergency help")
    html = html.replace("More water damage services (smaller grid)", "More water damage services")

    # Remove call-card copy about sending requests (already replaced whole card)
    return html


def fix_contact(html: str, path: Path) -> str:
    if "contact" not in path.parts:
        return html

    # Remove form-card wrapper and its intro about the form
    html = re.sub(
        r'<div class="form-card"[^>]*>.*?(?=<section>|<h2>Before we arrive|</article>|</div>\s*</div>\s*</section>)',
        "",
        html,
        count=1,
        flags=re.S,
    )

    # If "Send us a request" heading remains with form already gone
    html = re.sub(
        r"<h2>Send us a request</h2>\s*<p>Not an emergency.*?</ul>\s*",
        "",
        html,
        flags=re.S,
    )

    panel = f'''<section class="section">
<div class="container">
<div class="contact-panel">
<h2>Ready for help?</h2>
<p>If water is still spreading, calling is the fastest way to get help. We will talk you through what to do while we get to you.</p>
{phone_btn()}
</div>
</div>
</section>
'''
    if "contact-panel" not in html:
        # Insert after trust bar
        html = re.sub(
            r'(</section>\s*)(<section class="section">)',
            rf"\1{panel}\2",
            html,
            count=1,
        )
    return html


def fix_cost_guide_link(html: str) -> str:
    # Remove "or send us a request" links that point to contact form
    html = re.sub(
        r'\s*or <a href="/contact/">send us a request\.?</a>',
        "",
        html,
        flags=re.I,
    )
    html = re.sub(
        r'<a href="/contact/">send us a request\.?</a>',
        '<a href="tel:+16235550148">(623) 555-0148</a>',
        html,
        flags=re.I,
    )
    return html


def fix_about(html: str, path: Path) -> str:
    if "about" not in path.parts:
        return html
    html = re.sub(r'class="card"(?! topic-card)', 'class="card topic-card"', html)
    return html


def process(path: Path) -> bool:
    original = path.read_text(encoding="utf-8")
    html = original
    html = remove_forms(html)
    html = remove_waterlines(html)
    html = remove_form_ctas(html)
    html = replace_call_cards(html)
    html = replace_mobile_bar(html)
    html = replace_tel_buttons(html)
    html = strip_call_word_in_dark_cta(html)
    html = fix_homepage(html, path)
    html = fix_contact(html, path)
    html = fix_about(html, path)
    html = fix_cost_guide_link(html)
    html = re.sub(r"\n{3,}", "\n\n", html)

    if html != original:
        path.write_text(html, encoding="utf-8", newline="\n")
        return True
    return False


def main():
    changed = []
    for path in html_files():
        if process(path):
            changed.append(str(path.relative_to(ROOT)))
    print(f"Updated {len(changed)} files")

    # Sanity: pages must still have <main> with substantial content
    bad = []
    for path in html_files():
        t = path.read_text(encoding="utf-8")
        if "<main" in t and "</main>" in t:
            body = t.split("<main", 1)[1].split("</main>", 1)[0]
            if len(body) < 400 and path.name != "404.html":
                bad.append(f"SHORT BODY {path.relative_to(ROOT)} ({len(body)} chars)")
        for needle in ("lead-form", "Send my request", "waterline", 'href="#request"', "form-card"):
            if needle in t:
                bad.append(f"{path.relative_to(ROOT)}: {needle}")
        # Broken: Call word still in btn--call
        if re.search(r'btn--call[^>]*>[^<]*Call \(623\)', t):
            bad.append(f"{path.relative_to(ROOT)}: Call still in button")

    if bad:
        print("Problems:")
        for b in bad:
            print(" !", b)
    else:
        print("OK: forms/waterlines gone, bodies intact, buttons cleaned.")


if __name__ == "__main__":
    main()
