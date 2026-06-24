"""
Pre-render clinic data into each region's static HTML page.

This solves the Googlebot crawlability problem: the site currently renders
clinic listings via client-side JS fetching from Supabase, so Google's
Wave 1 (HTML-only) crawl sees an empty <div id="dentist-grid">.

What this script does:
  1. Fetches all clinics + pricing from Supabase (using service key for speed).
  2. For each live region page, injects:
       a) <script id="dc-prefetch">window.__DC_PREFETCH__ = {...}</script>
          directly before </head>, so the JS can skip the Supabase fetch
          entirely on page load (faster UX, no loading spinner).
       b) Three JSON-LD <script type="application/ld+json"> blocks:
            - BreadcrumbList  (Home > Region — improves search result display)
            - ItemList        (names all listed clinics for Google)
            - FAQPage         (can earn expandable FAQ snippets in results)
       c) Pre-rendered clinic card HTML inside <div id="dentist-grid">,
          so Google Wave 1 sees every practice name without needing JS.
       d) A visible FAQ section between </section> and <!-- Footer -->,
          required by Google policy — FAQPage schema must match visible content.
  3. Applies the same suburb-filter logic as SUBURB_FILTERS in app.js,
     so christchurch.html only shows Christchurch suburbs, etc.

Run before every push to GitHub:
    python build/prerender.py

Output: modifies docs/*.html in-place. The script is fully idempotent —
it strips all previously-injected blocks before re-injecting.
"""

import html
import json
import os
import re
import sys

import requests
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding="utf-8")
load_dotenv()

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_SERVICE_KEY"]
HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
}

DOCS = "docs"
BASE_URL = "https://dentalcompare.co.nz"

# ---------------------------------------------------------------------------
# Page config: filename -> (region, suburb_filter_key, breadcrumb_label)
# suburb_filter_key matches keys in SUBURB_FILTERS below (None = whole region).
# breadcrumb_label is the human-readable region name used in BreadcrumbList.
# ---------------------------------------------------------------------------
PAGES = {
    "index.html":               None,
    "auckland.html":            ("Auckland",            None,                  "Auckland"),
    "christchurch.html":        ("Canterbury",          "christchurch-city",   "Christchurch"),
    "wellington.html":          ("Wellington",          None,                  "Wellington"),
    "hamilton.html":            ("Waikato",             "hamilton-city",       "Hamilton"),
    "tauranga.html":            ("Bay of Plenty",       "tauranga-city",       "Tauranga"),
    "dunedin.html":             ("Otago",               "dunedin-city",        "Dunedin"),
    "manawatu-whanganui.html":  ("Manawatū-Whanganui", None,                  "Manawatū-Whanganui"),
    "northland.html":           ("Northland",           None,                  "Northland"),
    "hawkes-bay.html":          ("Hawke's Bay",         None,                  "Hawke's Bay"),
    "wider-bop.html":           ("Bay of Plenty",       "wider-bop",           "Bay of Plenty"),
    "taranaki.html":            ("Taranaki",            None,                  "Taranaki"),
    "nelson-tasman.html":       ("Nelson & Tasman",     None,                  "Nelson & Tasman"),
    "wider-waikato.html":       ("Waikato",             "wider-waikato",       "Wider Waikato"),
    "southland.html":           ("Southland",           None,                  "Southland"),
    "wider-otago.html":         ("Otago",               "wider-otago",         "Wider Otago"),
    "wider-canterbury.html":    ("Canterbury",          "wider-canterbury",    "Wider Canterbury"),
    "gisborne.html":            ("Gisborne",            None,                  "Gisborne"),
    "marlborough.html":         ("Marlborough",         None,                  "Marlborough"),
    "wairarapa.html":           ("Wairarapa",           None,                  "Wairarapa"),
    "west-coast.html":          ("West Coast",          None,                  "West Coast"),
}

# Mirrors SUBURB_FILTERS in docs/assets/js/app.js
SUBURB_FILTERS = {
    "christchurch-city": {
        "Christchurch Central","Papanui","Riccarton","Strowan","Merivale","St Albans",
        "Sydenham","Bishopdale","Linwood","Shirley","Spreydon","Hornby","Burnside",
        "Woolston","Avonhead","Hillmorton","Cashmere","Sockburn","Halswell",
        "Bryndwr","Richmond","Redwood","Riccarton (Upper)","Somerfield","Hoon Hay",
        "Phillipstown","Ferrymead","Casebrook","Northcote","Ilam","Waltham","Addington",
        "North New Brighton","Redcliffs","Fendalton","Yaldhurst",
        "Kaiapoi","Prebbleton","Rangiora","Rolleston","Lincoln",
    },
    "wider-canterbury": {"Ashburton","Timaru","Darfield","Geraldine","Kaikōura","Oxford"},
    "hamilton-city": {
        "Hamilton Central","Hamilton East","Claudelands","Chartwell","Hillcrest","Pukete",
        "Nawton","Fairfield","Whitiora","Hamilton Lake","Te Rapa","Rototuna North","Rototuna",
        "Frankton","Dinsdale","Beerescourt","Parkwood","Melville","Flagstaff",
    },
    "wider-waikato": {
        "Cambridge","Taupo","Thames","Te Awamutu","Morrinsville","Tokoroa","Waihi",
        "Pirongia","Leamington","Paeroa","Huntly","Coromandel Town","Matamata",
        "Raglan","Te Aroha","Turangi","Whitianga",
    },
    "tauranga-city": {
        "Tauranga","Papamoa Beach","Tauranga South","Gate Pa","Bethlehem","Greerton",
        "Pyes Pa","Otūmoetai","Papamoa","Mount Maunganui","Tauriko","Hairini",
    },
    "wider-bop": {"Rotorua","Whakatāne","Kawerau","Ōpōtiki","Katikati","Omokoroa","Te Puke"},
    "dunedin-city": {
        "Dunedin Central","Dunedin North","Mosgiel","Green Island","Roslyn","Wakari",
        "Musselburgh","North East Valley","Kaikorai","Mornington","South Dunedin","Maori Hill",
    },
    "wider-otago": {
        "Queenstown","Frankton","Wānaka","Alexandra","Oamaru","Cromwell",
        "Balclutha","Ranfurly","Milton","Palmerston",
    },
}

# ---------------------------------------------------------------------------
# FAQ content — same on every region page.
# Answers must be plain text (no HTML); they appear both in visible HTML
# and in the FAQPage JSON-LD schema block.
# ---------------------------------------------------------------------------
FAQ_ITEMS = [
    (
        "Why don't all clinics list prices?",
        "Dental fees vary depending on the complexity of treatment, the materials used, "
        "and each patient's individual needs, so many practices prefer to give a personalised "
        "quote after an examination. We publish prices wherever clinics have shared them "
        "publicly. If a clinic doesn't show prices, we recommend calling before your appointment.",
    ),
    (
        "Why did you make this website?",
        "Dental care in New Zealand can be expensive, and it's surprisingly hard to compare "
        "clinics or find one that's upfront about pricing. We built Dental Compare so that "
        "New Zealanders can see prices, read real patient reviews, and find the right practice "
        "for their needs, all in one place. We think transparency is good for patients and "
        "good for the clinics that deserve to stand out.",
    ),
    (
        "How are the reviews sourced?",
        "Reviews are pulled directly from Google, so they come from real patients who visited "
        "the clinic. We don't accept reviews submitted through this site. The rating and review "
        "count you see matches what you'd find on Google Maps.",
    ),
    (
        "How often is the information updated?",
        "We update clinic listings regularly, including contact details, services, and pricing "
        "where available. If you spot something that looks out of date, let us know.",
    ),
    (
        "Why are some clinics missing phone numbers or websites?",
        "Some clinics haven't listed this information publicly, or their details weren't "
        "available when we last updated. Where possible we link directly to the clinic's own "
        "website so you can find current contact information.",
    ),
    (
        "Is dental care free in New Zealand?",
        "It depends on your age. Children up to and including Year 8 are seen by Community "
        "Dental Service therapists, usually at a school dental clinic. From Year 9 until their "
        "18th birthday, teenagers receive free dental care at private practices contracted to "
        "Health New Zealand, so the government pays the bill rather than the family. Not all "
        "clinics offer this, so you need to look for ones that do. You can filter for it on "
        "Dental Compare. At 18, dental treatment is "
        "no longer publicly funded, so costs are paid out of pocket unless you have health "
        "insurance that covers dental, or your treatment is ACC-eligible.",
    ),
    (
        "So some clinics won't provide free teen dental care?",
        "Correct. To offer free care for teenagers, a practice must hold an adolescent contract "
        "with Health New Zealand. Not all private dentists have one. When a teenager transitions "
        "from the school dental service at the start of Year 9, or when a family moves to a new "
        "area, they can't just walk into any practice and expect free care. It's worth calling "
        "ahead to check before booking.",
    ),
    (
        "Does ACC cover dental treatment?",
        "ACC covers dental treatment if your injury was caused by an accident, such as a "
        "chipped or knocked-out tooth from a fall or sports injury. Routine dental work, "
        "decay, and gum disease are not covered. Your dentist can help you lodge an ACC "
        "claim if your treatment qualifies.",
    ),
    (
        "Do any clinics offer payment plans?",
        "Many dental practices in New Zealand offer in-house payment plans or work with "
        "providers like Afterpay, Q Card, or Zip. You'll often find this on the clinic's "
        "profile page. If it's not listed, it's worth asking when you call.",
    ),
    (
        "What's the difference between a dentist and a dental hygienist?",
        "A dentist diagnoses and treats dental conditions, including fillings, extractions, "
        "root canals, and cosmetic work. A dental hygienist focuses on preventive care, "
        "mainly teeth cleaning, scaling, and oral hygiene advice. Many practices have both. "
        "If you're only after a clean, booking with the hygienist is usually faster and cheaper.",
    ),
    (
        "How do I find an emergency dentist?",
        "Most dental practices set aside time for same-day emergency appointments. Search "
        "for clinics near you, check their profile for emergency availability, and call as "
        "early in the day as possible as slots fill quickly. Some practices also list an "
        "after-hours contact number.",
    ),
    (
        "What should I look for when choosing a dentist?",
        "Location and hours that work for you, clear pricing, and a good number of recent "
        "positive reviews are a solid starting point. If you have dental anxiety, look for "
        "practices that mention this specifically. It's also worth checking what services "
        "they offer in-house, as some treatments may need a referral elsewhere.",
    ),
    (
        "Can I trust the star ratings?",
        "The ratings shown are Google reviews from real patients and can't be submitted "
        "through this site. When comparing clinics, look at the number of reviews as well "
        "as the score. A clinic with 4.8 stars from 200 reviews is generally more reliable "
        "than one with 5 stars from 3.",
    ),
    (
        "Why do some clinics have no reviews?",
        "Newer practices or smaller clinics in less populated areas often have few or no "
        "reviews. Absence of reviews doesn't mean a clinic is poor. It may simply be new "
        "or serve a small community where patients don't tend to leave online feedback.",
    ),
]


# ---------------------------------------------------------------------------
# Supabase data fetching
# ---------------------------------------------------------------------------

def fetch_all_clinics():
    clinics = []
    limit = 1000
    offset = 0
    while True:
        url = (
            f"{SUPABASE_URL}/rest/v1/dental_clinics"
            f"?business_status=eq.OPERATIONAL"
            f"&order=region,total_ratings.desc.nullslast"
            f"&limit={limit}&offset={offset}"
        )
        r = requests.get(url, headers=HEADERS, timeout=30)
        r.raise_for_status()
        batch = r.json()
        clinics.extend(batch)
        if len(batch) < limit:
            break
        offset += limit
    return clinics


def fetch_pricing_for_ids(clinic_ids: list[int]) -> dict:
    if not clinic_ids:
        return {}
    pricing: dict[int, list] = {}
    chunk = 200
    for i in range(0, len(clinic_ids), chunk):
        ids_param = ",".join(f"clinic_id.eq.{cid}" for cid in clinic_ids[i:i+chunk])
        offset = 0
        limit = 1000
        while True:
            url = (
                f"{SUPABASE_URL}/rest/v1/scraped_prices"
                f"?or=({ids_param})"
                f"&select=clinic_id,treatment,price_label,notes"
                f"&order=clinic_id,id"
                f"&limit={limit}&offset={offset}"
            )
            r = requests.get(url, headers=HEADERS, timeout=30)
            r.raise_for_status()
            rows = r.json()
            for row in rows:
                cid = row["clinic_id"]
                pricing.setdefault(cid, []).append({
                    "service": row.get("treatment", ""),
                    "price":   row.get("price_label", ""),
                    "notes":   row.get("notes", ""),
                })
            if len(rows) < limit:
                break
            offset += limit
    return pricing


# ---------------------------------------------------------------------------
# HTML card generation (mirrors cardHTML() in app.js)
# ---------------------------------------------------------------------------

def stars_html(rating: float) -> str:
    full  = int(rating)
    half  = 1 if (rating - full) >= 0.25 else 0
    empty = 5 - full - half
    return "★" * full + "½" * half + "☆" * empty


def card_html(clinic: dict, pricing: list, region: str) -> str:
    name    = clinic.get("name") or "Unknown Clinic"
    suburb  = clinic.get("suburb_town") or clinic.get("town") or ""
    city    = clinic.get("city") or ""
    if city == "NA":
        city = ""
    rating       = clinic.get("rating") or 0
    review_count = clinic.get("total_ratings") or 0
    phone        = (
        clinic.get("phone_national") or
        clinic.get("phone_international") or
        clinic.get("phone") or ""
    )
    services_raw = clinic.get("services") or "General Dentistry"
    services     = [s.strip() for s in services_raw.split(",")]
    if "Teen Dental" in services:
        services = ["Teen Dental"] + [s for s in services if s != "Teen Dental"]
    cid          = clinic["id"]

    initials = "".join(w[0] for w in name.split() if w)[:2].upper()
    location = (
        f"{suburb}, {city}" if suburb and city and suburb != city
        else city or suburb or "Unknown"
    )
    rating_display = (
        f'<span class="stars">{stars_html(rating)}</span> <strong>{rating}</strong>'
        if rating else '<span style="color:var(--clr-gray-400)">No rating yet</span>'
    )
    review_text = (
        f'💬 {review_count} review{"" if review_count == 1 else "s"}'
        if review_count else ""
    )
    service_pills = "".join(
        f'<span class="pill pill--sm">{html.escape(s)}</span>'
        for s in services[:4]
    )
    pricing_preview = ""
    if pricing:
        rows_html = "".join(
            f'<div class="pricing-preview__row">'
            f'<span>{html.escape(p["service"])}</span>'
            f'<span class="pricing-preview__price">{html.escape(p["price"])}</span>'
            f'</div>'
            for p in pricing[:3]
        )
        more = (
            f'<div class="pricing-preview__more">+ {len(pricing)-3} more services</div>'
            if len(pricing) > 3 else ""
        )
        pricing_preview = f'<div class="pricing-preview">{rows_html}{more}</div>'

    phone_text = ""
    if phone:
        phone_clean = re.sub(r"\s", "", phone)
        phone_text = (
            f'<a href="tel:{phone_clean}" style="text-decoration:none; color:inherit;">'
            f'📞 {html.escape(phone)}</a>'
        )

    profile_link = f"dentist.html?id={cid}&region={requests.utils.quote(region)}"

    return (
        f'        <article class="dentist-card" '
        f'data-suburb="{html.escape(suburb)}" '
        f'data-rating="{rating}" '
        f'data-name="{html.escape(name)}">\n'
        f'          <div class="dentist-card__avatar">{initials}</div>\n'
        f'          <div class="dentist-card__body">\n'
        f'            <h3 class="dentist-card__name">'
        f'<a href="{profile_link}">{html.escape(name)}</a></h3>\n'
        f'            <div class="dentist-card__meta">\n'
        f'              <span class="dentist-card__meta-item">{rating_display}</span>\n'
        f'              <span class="dentist-card__meta-item">📍 {html.escape(location)}</span>\n'
        + (f'              <span class="dentist-card__meta-item">{review_text}</span>\n' if review_text else "")
        + f'            </div>\n'
        + (f'            <div class="dentist-card__services">{service_pills}</div>\n' if service_pills else "")
        + pricing_preview + "\n"
        f'            <div class="dentist-card__footer">\n'
        f'              <div>'
        + (f'<span class="dentist-card__phone">{phone_text}</span>' if phone_text else "")
        + f'</div>\n'
        f'              <a href="{profile_link}" class="btn btn--primary">View Profile</a>\n'
        f'            </div>\n'
        f'          </div>\n'
        f'        </article>'
    )


# ---------------------------------------------------------------------------
# Structured data (JSON-LD)
# ---------------------------------------------------------------------------

def schema_ld(filename: str, label: str, clinics: list[dict], region: str) -> str:
    page_url = f"{BASE_URL}/{filename}"

    breadcrumb = {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Home",
             "item": f"{BASE_URL}/"},
            {"@type": "ListItem", "position": 2, "name": f"Dentists in {label}",
             "item": page_url},
        ],
    }

    item_list = {
        "@context": "https://schema.org",
        "@type": "ItemList",
        "name": f"Dentists in {label}",
        "url": page_url,
        "numberOfItems": len(clinics),
        "itemListElement": [
            {
                "@type": "ListItem",
                "position": i + 1,
                "item": {
                    "@type": "Dentist",
                    "name": c.get("name", ""),
                    "url": f"{BASE_URL}/dentist.html?id={c['id']}&region={requests.utils.quote(region)}",
                    **({"telephone": c["phone_national"]} if c.get("phone_national") else {}),
                },
            }
            for i, c in enumerate(clinics)
        ],
    }

    faq_schema = {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {
                "@type": "Question",
                "name": q,
                "acceptedAnswer": {"@type": "Answer", "text": a},
            }
            for q, a in FAQ_ITEMS
        ],
    }

    def ld_tag(obj: dict) -> str:
        return (
            '<script type="application/ld+json">\n'
            + json.dumps(obj, ensure_ascii=False, indent=2)
            + '\n</script>'
        )

    return "\n    ".join([ld_tag(breadcrumb), ld_tag(item_list), ld_tag(faq_schema)])


# ---------------------------------------------------------------------------
# Visible FAQ section HTML
# ---------------------------------------------------------------------------

def faq_section_html() -> str:
    items = ""
    for q, a in FAQ_ITEMS:
        items += (
            f'        <details class="faq__item">\n'
            f'            <summary class="faq__question">{html.escape(q)}</summary>\n'
            f'            <p class="faq__answer">{html.escape(a)}</p>\n'
            f'        </details>\n'
        )
    return (
        '\n    <!-- dc-faq-start -->\n'
        '    <section class="faq section">\n'
        '        <div class="container">\n'
        '            <h2 class="faq__heading">Frequently Asked Questions</h2>\n'
        + items +
        '        </div>\n'
        '    </section>\n'
        '    <!-- dc-faq-end -->'
    )


# ---------------------------------------------------------------------------
# HTML injection
# ---------------------------------------------------------------------------

PREFETCH_RE = re.compile(
    r'\s*<!-- dc-prefetch-start -->.*?<!-- dc-prefetch-end -->',
    re.DOTALL,
)
SCHEMA_RE = re.compile(
    r'\s*<!-- dc-schema-start -->.*?<!-- dc-schema-end -->',
    re.DOTALL,
)
CARDS_RE = re.compile(
    r'<!-- dc-cards-start -->.*?<!-- dc-cards-end -->',
    re.DOTALL,
)
FAQ_RE = re.compile(
    r'\s*<!-- dc-faq-start -->.*?<!-- dc-faq-end -->',
    re.DOTALL,
)
GRID_OPEN_RE = re.compile(r'(<div[^>]+id="dentist-grid"[^>]*>)')


def inject_page(
    path: str,
    clinics: list[dict],
    pricing_map: dict,
    region: str,
    filename: str,
    label: str,
):
    with open(path, encoding="utf-8") as f:
        src = f.read()

    # Strip all previously-injected blocks (makes script fully idempotent)
    src = PREFETCH_RE.sub("", src)
    src = SCHEMA_RE.sub("", src)
    src = FAQ_RE.sub("", src)

    # --- 1. Prefetch JSON block ---
    KEEP = {
        "id","name","suburb_town","town","city",
        "phone_national","phone_international","phone",
        "rating","total_ratings","services","price","description",
    }
    slim_clinics = [{k: c[k] for k in KEEP if k in c} for c in clinics]
    slim_pricing = {
        str(cid): rows
        for cid, rows in pricing_map.items()
        if cid in {c["id"] for c in clinics}
    }
    prefetch_json = json.dumps(
        {"clinics": slim_clinics, "pricing": slim_pricing},
        ensure_ascii=False, separators=(",", ":"),
    )
    prefetch_block = (
        '\n    <!-- dc-prefetch-start -->\n'
        '    <script id="dc-prefetch">window.__DC_PREFETCH__='
        + prefetch_json + ';</script>\n'
        '    <!-- dc-prefetch-end -->'
    )

    # --- 2. JSON-LD schema block ---
    schema_block = (
        '\n    <!-- dc-schema-start -->\n    '
        + schema_ld(filename, label, clinics, region)
        + '\n    <!-- dc-schema-end -->'
    )

    # Inject both before </head>
    src = src.replace(
        "</head>",
        prefetch_block + schema_block + "\n</head>",
        1,
    )

    # --- 3. Pre-rendered clinic cards ---
    cards_html = "\n".join(
        card_html(c, pricing_map.get(c["id"], []), region)
        for c in clinics
    )
    cards_block = f"<!-- dc-cards-start -->\n{cards_html}\n      <!-- dc-cards-end -->"

    if CARDS_RE.search(src):
        src = CARDS_RE.sub(cards_block, src, count=1)
    elif GRID_OPEN_RE.search(src):
        src = GRID_OPEN_RE.sub(
            lambda m: m.group(1) + "\n" + cards_block,
            src, count=1,
        )
    else:
        print(f"  WARNING: no dentist-grid found in {path}")

    # --- 4. Visible FAQ section ---
    faq_block = faq_section_html()
    if "<!-- Footer -->" in src:
        src = src.replace("<!-- Footer -->", faq_block + "\n\n    <!-- Footer -->", 1)
    elif '<footer class="footer">' in src:
        src = src.replace('<footer class="footer">', faq_block + '\n\n    <footer class="footer">', 1)
    else:
        print(f"  WARNING: no footer marker found in {path}")

    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(src)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("Fetching all clinics from Supabase…")
    all_clinics = fetch_all_clinics()
    print(f"  {len(all_clinics)} clinics loaded")

    by_region: dict[str, list] = {}
    for c in all_clinics:
        by_region.setdefault(c.get("region", ""), []).append(c)

    print("Fetching pricing…")
    all_ids = [c["id"] for c in all_clinics]
    pricing_map = fetch_pricing_for_ids(all_ids)
    print(f"  Pricing loaded for {len(pricing_map)} clinics")

    for filename, page_cfg in PAGES.items():
        if page_cfg is None:
            continue
        region, suburb_filter_key, label = page_cfg

        region_clinics = by_region.get(region, [])
        if not region_clinics:
            print(f"  WARNING: no clinics for region '{region}' ({filename})")
            continue

        if suburb_filter_key:
            allowed = SUBURB_FILTERS.get(suburb_filter_key, set())
            filtered = [
                c for c in region_clinics
                if (c.get("suburb_town") or c.get("town") or "") in allowed
            ]
        else:
            filtered = region_clinics

        path = os.path.join(DOCS, filename)
        inject_page(path, filtered, pricing_map, region, filename, label)
        print(f"  {filename}: {len(filtered)} clinics, schema + FAQ injected")

    print("\nDone. Run 'git diff --stat docs/' to review changes before pushing.")


if __name__ == "__main__":
    main()
