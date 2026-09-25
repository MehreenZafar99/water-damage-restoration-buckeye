#!/usr/bin/env python3
"""Ensure every footer has email + address block."""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
ICON = (
    '<svg viewBox="0 0 24 24" aria-hidden="true">'
    '<path fill="currentColor" d="M6.6 10.8a15.1 15.1 0 0 0 6.6 6.6l2.2-2.2a1 1 0 0 1 1-.25'
    'c1.1.37 2.3.57 3.6.57a1 1 0 0 1 1 1V20a1 1 0 0 1-1 1A17 17 0 0 1 3 4a1 1 0 0 1 1-1'
    'h3.5a1 1 0 0 1 1 1c0 1.25.2 2.45.57 3.57a1 1 0 0 1-.25 1z"/></svg>'
)
BTN = f'<a class="btn btn--call btn--call-inline" href="tel:+16235550148">{ICON} (623) 555-0148</a>'
BLOCK = f'''        <div class="footer-contact">
          {BTN}
          <p class="footer-meta"><a href="mailto:contact@waterdamagerestorationbuckeyeaz.com">contact@waterdamagerestorationbuckeyeaz.com</a><br>21430 W Yuma Rd, Suite 120, Buckeye, AZ 85326<br>Open 24 hours, 7 days a week<br>Serving Buckeye, AZ 85326 and 85396</p>
        </div>'''

# Replace old phone-only paragraph in footer-brand
OLD = re.compile(
    r'<p>(?:<a class="(?:btn[^"]*|footer-phone)"[^>]*>.*?</a>|<a class="btn[^"]*"[^>]*>.*?</a>)<br>Open 24 hours, 7 days a week<br>Serving Buckeye, AZ 85326 and 85396</p>',
    re.S,
)
OLD2 = re.compile(
    r'<p><a class="btn[^"]*" href="tel:\+16235550148">.*?</a><br>Open 24 hours, 7 days a week<br>Serving Buckeye, AZ 85326 and 85396</p>',
    re.S,
)

n = 0
for p in ROOT.rglob("*.html"):
    if "files" in p.parts or "content" in p.parts:
        continue
    t = p.read_text(encoding="utf-8")
    if "site-footer" not in t:
        continue
    if "contact@waterdamagerestorationbuckeyeaz.com" in t and "21430 W Yuma Rd" in t:
        continue
    nt = OLD2.sub(BLOCK, t, count=1)
    if nt == t:
        # more generic: after brand blurb paragraph, replace next p or insert
        nt = re.sub(
            r'(helps Buckeye homes and businesses recover from water damage, day or night\.</p>)\s*<p>.*?</p>',
            rf"\1\n{BLOCK}",
            t,
            count=1,
            flags=re.S,
        )
    if nt != t:
        p.write_text(nt, encoding="utf-8", newline="\n")
        n += 1
        print("fixed", p)
print("done", n)
