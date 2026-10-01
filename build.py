#!/usr/bin/env python3
"""Builds the policy pages from content/*.html fragments.

Edit wording in content/, then run:  python3 build.py
"""
from pathlib import Path

ROOT = Path(__file__).parent

POLICIES = [
    # slug, title, source fragment (None = external document)
    ("complaints", "Complaints", "complaints.html"),
    ("privacy-notice", "Privacy Notice", "privacy-notice.html"),
    ("regulatory", "Regulatory &amp; Disclaimer", "regulatory.html"),
    ("terms-and-conditions", "Website Terms &amp; Conditions", "terms-and-conditions.html"),
]
PDF = ("Standard Terms and Conditions", "assets/docs/standard-terms-and-conditions.pdf")
COOKIES = ("cookies", "Cookies Policy", "cookies.html")



def page(title, rel, crumbs, body, description):
    crumb_html = "".join(
        f'<li><a href="{href}">{label}</a></li>' if href else f'<li aria-current="page">{label}</li>'
        for label, href in crumbs
    )
    plain = title.replace("&amp;", "&")
    return f"""<!doctype html>
<html lang="en-GB">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{plain} | Twenty4</title>
  <meta name="description" content="{description}">
  <meta name="theme-color" content="#050b1f">
  <link rel="icon" href="{rel}assets/favicon.svg" type="image/svg+xml">
  <link rel="icon" href="{rel}assets/favicon-32.png" sizes="32x32" type="image/png">
  <link rel="apple-touch-icon" href="{rel}assets/apple-touch-icon.png">
  <meta name="robots" content="noindex, nofollow">
  <link rel="stylesheet" href="{rel}css/site.css">
  <script src="{rel}js/gate.js"></script>
</head>
<body>
  <a class="skip" href="#main">Skip to content</a>
  <header class="bar">
    <div class="wrap">
      <a class="logo" href="{rel}"><img src="{rel}assets/twenty4-logo-rev.svg" alt="Twenty4" width="164" height="38"></a>
      <a class="bar-link" href="{rel}#contact"><svg class="bar-icon" viewBox="0 0 120 120" aria-hidden="true"><path fill="none" stroke="currentColor" stroke-width="9" stroke-linecap="butt" stroke-linejoin="miter" d="M16 30H104V90H16Z M30 44L60 66L90 44"/></svg><span>Enquiries</span></a>
    </div>
  </header>
  <main id="main">
    <section class="page-head">
      <div class="wrap">
        <ol class="crumbs">{crumb_html}</ol>
        <h1 class="page-title">{title}</h1>
      </div>
    </section>
    <section class="paper">
      <div class="wrap">
{body}
      </div>
    </section>
  </main>
  <footer class="site-footer">
    <div class="wrap">
      <a class="logo" href="{rel}"><img src="{rel}assets/twenty4-logo-rev.svg" alt="Twenty4" width="104" height="24"></a>
      <ul class="footer-nav">
        <li><a href="{rel}policies/">Policies</a></li>
        <li><a href="{rel}cookies/">Cookies Policy</a></li>
      </ul>
      <div class="footer-legal small">
        <p>Licensed by the Guernsey Financial Services Commission (GFSC ref 3078). Fort Management Services Limited, registered in Guernsey no. 7396.</p>
        <p>&copy; <span data-year>2026</span> Twenty4</p>
      </div>
    </div>
  </footer>
  <script src="{rel}js/site.js" defer></script>
</body>
</html>
"""


def sidebar(rel, current):
    items = [(s, t, f"{rel}policies/{s}/") for s, t, _ in POLICIES]
    items.append((COOKIES[0], COOKIES[1], f"{rel}cookies/"))
    cur = ' aria-current="page"'
    links = "".join(
        f'<li><a href="{href}"{cur if s == current else ""}>{t}</a></li>'
        for s, t, href in items
    )
    links += f'<li><a href="{rel}{PDF[1]}" download>{PDF[0]} (PDF)</a></li>'
    return f'<aside aria-label="Policies"><ul>{links}</ul></aside>'


def article(rel, slug, fragment):
    content = (ROOT / "content" / fragment).read_text().strip()
    return f'        <div class="article">{sidebar(rel, slug)}<article class="legal">\n{content}\n</article></div>'


def write(path, html):
    out = ROOT / path
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html)
    print("wrote", path)


# Policies index
rows = []
entries = [(t, f"{s}/", "") for s, t, _ in POLICIES]
entries.append((COOKIES[1], "../cookies/", ""))
entries.append((PDF[0], f"../{PDF[1]}", "PDF, 165 KB"))
for t, href, meta in entries:
    attr = " download" if meta else ""
    tag = f'<span class="meta">{meta}</span>' if meta else ""
    rows.append(f'<li><a href="{href}"{attr}><span class="t">{t}</span>{tag}</a></li>')
write("policies/index.html", page(
    "Policies", "../",
    [("Home", "../"), ("Policies", None)],
    f'        <ul class="policy-list">{"".join(rows)}</ul>',
    "Twenty4 policies: complaints, privacy notice, regulatory information and terms and conditions.",
))

for slug, title, fragment in POLICIES:
    write(f"policies/{slug}/index.html", page(
        title, "../../",
        [("Home", "../../"), ("Policies", "../"), (title, None)],
        article("../../", slug, fragment),
        f"Twenty4 {title.replace('&amp;', 'and')}.",
    ))

slug, title, fragment = COOKIES
write("cookies/index.html", page(
    title, "../",
    [("Home", "../"), (title, None)],
    article("../", slug, fragment),
    "How the Twenty4 website uses cookies.",
))
