"""
Generates a single static docs/clinic/<slug>/index.html page for one clinic,
matching the existing template (see docs/clinic/32-gems-dental-care/index.html).

The page itself is mostly boilerplate - the actual profile content is rendered
client-side by app.js from window.__CLINIC_ID__. What this script fills in is
just the SEO-facing bits: <title>, meta description, canonical URL, and the
JSON-LD schema block.

The slug MUST exactly match dcClinicSlug()/dcSlugBase() in assets/js/app.js,
since that's what clinicUrl() uses to build "View Profile" links site-wide -
mismatch here means a 404, which is exactly what this script exists to avoid.

Usage: python build/generate_clinic_page.py <clinic_id>
"""
import html
import json
import os
import re
import sys

import requests

SUPABASE_URL = "https://ydcminsdkiccbngkbvpg.supabase.co"
ANON_KEY = "sb_publishable_ikGnFs7m_Q8oIJLOddKuSg_6A8Mkoed"

DC_COLLISIONS = {
    "central-dental", "dental-reflections", "lumino-implant-centre", "northmed-dental",
    "nsoms-oral-maxillofacial-surgeons", "phoenix-house-dental-centre",
    "queen-street-dental-centre", "rapid-response-dental", "supreme-dental-concepts",
    "tam-dental-group-cosmetic-general-dentistry", "teeth-whitening-associates",
    "the-denture-man",
}


def slug_base(s):
    s = (s or "").lower()
    s = re.sub(r"[^a-z0-9\s-]", "", s)
    s = s.replace(" ", "-")
    s = re.sub(r"-+", "-", s)
    return s.strip("-")


def clinic_slug(name, suburb):
    b = slug_base(name)
    if b in DC_COLLISIONS:
        return (b + "-" + slug_base(suburb)).strip("-")
    return b


def fetch_clinic(clinic_id):
    r = requests.get(
        f"{SUPABASE_URL}/rest/v1/dental_clinics",
        headers={"apikey": ANON_KEY},
        params={"id": f"eq.{clinic_id}", "select": "*"},
        verify=False,
    )
    r.raise_for_status()
    rows = r.json()
    if not rows:
        raise SystemExit(f"No clinic found with id {clinic_id}")
    return rows[0]


def build_page(c):
    name = c["name"]
    suburb = c.get("suburb_town") or ""
    city = c.get("city") or ""
    region = c.get("region") or ""
    locality = f"{suburb}, {city}" if suburb and city else (city or suburb or region)
    slug = clinic_slug(name, suburb)

    title = f"{html.escape(name)} — Dentist in {html.escape(suburb or city)} | Dental Compare"
    desc = f"{name} in {locality}. See services, prices, opening hours and patient reviews on Dental Compare."
    desc_escaped = html.escape(desc)
    canonical = f"https://dentalcompare.co.nz/clinic/{slug}"

    schema = {
        "@context": "https://schema.org",
        "@type": "Dentist",
        "name": name,
        "url": canonical,
        "address": {
            "@type": "PostalAddress",
            "streetAddress": c.get("address") or "",
            "addressLocality": city or suburb,
            "addressRegion": region,
            "addressCountry": "NZ",
        },
    }
    if c.get("phone_national"):
        schema["telephone"] = c["phone_national"]
    if c.get("website"):
        schema["sameAs"] = [c["website"]]
    if c.get("rating") and c.get("total_ratings"):
        schema["aggregateRating"] = {
            "@type": "AggregateRating",
            "ratingValue": c["rating"],
            "reviewCount": c["total_ratings"],
        }

    schema_json = json.dumps(schema, ensure_ascii=False, indent=2)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <link rel="icon" href="/assets/images/favicon.ico" sizes="any"><link rel="apple-touch-icon" href="/assets/images/favicon-192.png">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <script async src="https://www.googletagmanager.com/gtag/js?id=G-4J758VJQVX"></script>
    <script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments);}}gtag('js',new Date());gtag('config','G-4J758VJQVX');</script>
    <script type="text/javascript">(function(c,l,a,r,i,t,y){{c[a]=c[a]||function(){{(c[a].q=c[a].q||[]).push(arguments)}};t=l.createElement(r);t.async=1;t.src="https://www.clarity.ms/tag/"+i;y=l.getElementsByTagName(r)[0];y.parentNode.insertBefore(t,y);}})(window,document,"clarity","script","xn7ylrmc33");</script>
    <title>{title}</title>
    <meta name="description" content="{desc_escaped}">
    <link rel="canonical" href="{canonical}">
    <meta property="og:title" content="{html.escape(name)} | Dental Compare">
    <meta property="og:description" content="{desc_escaped}">
    <meta property="og:type" content="website">
    <link rel="stylesheet" href="/assets/css/styles.css?v=23">
    <script type="application/ld+json">
{schema_json}
    </script>
</head>
<body>
    <header class="header">
        <div class="container header__inner">
            <a href="/" class="logo"><img src="/assets/images/logo.png" alt="Dental Compare" class="logo__img"></a>
            <nav class="nav" id="main-nav">
                <a href="/" class="nav__link">Home</a>
                <a href="/#locations" class="nav__link">Regions</a>
                <a href="/compare.html" class="nav__link">Compare</a>
                <div class="nav__more">
                    <button class="nav__more-btn" aria-haspopup="true">More &#9662;</button>
                    <div class="nav__more-menu">
                        <a href="/saved.html" class="nav__link">Saved</a>
                        <a href="/faq.html" class="nav__link">FAQ</a>
                        <a href="/contact.html" class="nav__link">Contact</a>
                    </div>
                </div>
                <a href="/claim.html" class="nav__link nav__link--owners">Clinic owners</a>
            </nav>
            <button class="menu-toggle" id="menu-toggle" aria-label="Toggle menu"><span></span><span></span><span></span></button>
        </div>
    </header>
    <section class="profile-hero">
        <div class="container">
            <a href="/" class="profile-hero__back">&larr; Back to listings</a>
            <h1 id="profile-name">{html.escape(name)}</h1>
            <div class="profile-hero__meta" id="profile-meta"></div>
        </div>
    </section>
    <section class="section" style="padding-top: 0;">
        <div class="container">
            <div class="profile-layout" id="profile-content">
                <div class="no-results"><div class="no-results__icon">&#9203;</div><h3>Loading profile...</h3></div>
            </div>
        </div>
    </section>
    <footer class="footer"><div class="container"><div class="footer__copy">Built in New Zealand</div></div></footer>
    <script>window.__CLINIC_ID__ = {c['id']};</script>
    <script src="https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2/dist/umd/supabase.js"></script>
    <script src="/assets/js/dentists.js"></script>
    <script src="/assets/js/supabase.js"></script>
    <script src="/assets/js/app.js?v=45"></script>
    <script src="/assets/js/submit.js"></script>
    <script src="/assets/js/feedback.js"></script>
</body>
</html>
""", slug


def main():
    if len(sys.argv) != 2:
        raise SystemExit("Usage: python build/generate_clinic_page.py <clinic_id>")
    clinic_id = int(sys.argv[1])
    clinic = fetch_clinic(clinic_id)
    page, slug = build_page(clinic)

    out_dir = os.path.join(os.path.dirname(__file__), "..", "docs", "clinic", slug)
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "index.html")
    if os.path.exists(out_path):
        raise SystemExit(f"Refusing to overwrite existing page at {out_path} - remove it first if intentional.")

    with open(out_path, "w", encoding="utf-8") as f:
        f.write(page)
    print(f"Wrote {out_path} (slug: {slug})")


if __name__ == "__main__":
    main()
