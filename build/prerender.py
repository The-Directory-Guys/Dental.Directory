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
       b) Pre-rendered clinic card HTML inside <div id="dentist-grid">,
          so Google Wave 1 sees every practice name without needing JS.
  3. Applies the same suburb-filter logic as SUBURB_FILTERS in app.js,
     so christchurch.html only shows Christchurch suburbs, etc.

Run before every push to GitHub:
    python build/prerender.py

Output: modifies docs/*.html in-place (the script is idempotent -- it
strips any previously injected prefetch block before re-injecting).
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
# Use service key so we can paginate without rate-limit issues; data is
# identical to what the anon key returns (dental_clinics has public SELECT).
SUPABASE_KEY = os.environ["SUPABASE_SERVICE_KEY"]
HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
}

DOCS = "docs"

# Map of html file -> (region, suburb_filter_key | None)
# suburb_filter_key matches the keys in SUBURB_FILTERS in app.js.
PAGES = {
    "index.html":               None,   # home page — no clinic grid
    "auckland.html":            ("Auckland",              None),
    "christchurch.html":        ("Canterbury",            "christchurch-city"),
    "wellington.html":          ("Wellington",            None),
    "hamilton.html":            ("Waikato",               "hamilton-city"),
    "tauranga.html":            ("Bay of Plenty",         "tauranga-city"),
    "dunedin.html":             ("Otago",                 "dunedin-city"),
    "manawatu-whanganui.html":  ("Manawatū-Whanganui",   None),
    "northland.html":           ("Northland",             None),
    "hawkes-bay.html":          ("Hawke's Bay",           None),
    "wider-bop.html":           ("Bay of Plenty",         "wider-bop"),
    "taranaki.html":            ("Taranaki",              None),
    "nelson-tasman.html":       ("Nelson & Tasman",       None),
    "wider-waikato.html":       ("Waikato",               "wider-waikato"),
    "southland.html":           ("Southland",             None),
    "wider-otago.html":         ("Otago",                 "wider-otago"),
    "wider-canterbury.html":    ("Canterbury",            "wider-canterbury"),
    "gisborne.html":            ("Gisborne",              None),
    "marlborough.html":         ("Marlborough",           None),
    "wairarapa.html":           ("Wairarapa",             None),
    "west-coast.html":          ("West Coast",            None),
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
# Supabase data fetching
# ---------------------------------------------------------------------------

def fetch_all_clinics():
    """Fetch every OPERATIONAL clinic from dental_clinics, all regions."""
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
    """Fetch scraped_prices rows for the given clinic ids.
    Returns {clinic_id: [{treatment, price_label, notes}, ...]}."""
    if not clinic_ids:
        return {}
    pricing: dict[int, list] = {}
    chunk = 200          # PostgREST URL length limit
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
                    "service":  row.get("treatment", ""),
                    "price":    row.get("price_label", ""),
                    "notes":    row.get("notes", ""),
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
# HTML injection
# ---------------------------------------------------------------------------

# Matches the previously-injected prefetch block so the script is idempotent.
PREFETCH_RE = re.compile(
    r'\s*<!-- dc-prefetch-start -->.*?<!-- dc-prefetch-end -->',
    re.DOTALL,
)
# Matches the previously-injected cards block (between sentinel comments).
CARDS_RE = re.compile(
    r'<!-- dc-cards-start -->.*?<!-- dc-cards-end -->',
    re.DOTALL,
)
# Matches the dentist-grid opening tag (with any attributes) — used only on
# first run (before sentinel comments exist).
GRID_OPEN_RE = re.compile(r'(<div[^>]+id="dentist-grid"[^>]*>)')


def inject_page(path: str, clinics: list[dict], pricing_map: dict, region: str):
    with open(path, encoding="utf-8") as f:
        html_src = f.read()

    # Strip any previously-injected prefetch block
    html_src = PREFETCH_RE.sub("", html_src)

    # Build the prefetch JSON — only fields shown on listing cards.
    # opening_hours, address, email, website, google_maps_url are only needed
    # on the profile page, which fetches from Supabase separately, so we
    # omit them here to keep page size small (especially for Auckland ~490 clinics).
    KEEP = {
        "id","name","suburb_town","town","city",
        "phone_national","phone_international","phone",
        "rating","total_ratings","services","price","description",
    }
    slim_clinics = [{k: c[k] for k in KEEP if k in c} for c in clinics]
    slim_pricing = {str(cid): rows for cid, rows in pricing_map.items() if cid in {c["id"] for c in clinics}}

    prefetch_json = json.dumps(
        {"clinics": slim_clinics, "pricing": slim_pricing},
        ensure_ascii=False, separators=(",", ":"),
    )
    prefetch_block = (
        '\n    <!-- dc-prefetch-start -->\n'
        '    <script id="dc-prefetch">window.__DC_PREFETCH__='
        + prefetch_json +
        ';</script>\n'
        '    <!-- dc-prefetch-end -->'
    )

    # Inject prefetch block before </head>
    html_src = html_src.replace("</head>", prefetch_block + "\n</head>", 1)

    # Build pre-rendered card HTML wrapped in sentinel comments so subsequent
    # runs can find and replace the block precisely (avoids the nested-div
    # closing-tag ambiguity of a pure regex approach).
    cards_html = "\n".join(
        card_html(c, pricing_map.get(c["id"], []), region)
        for c in clinics
    )
    cards_block = f"<!-- dc-cards-start -->\n{cards_html}\n      <!-- dc-cards-end -->"

    if CARDS_RE.search(html_src):
        # Subsequent runs: replace between the sentinel comments.
        new_html = CARDS_RE.sub(cards_block, html_src, count=1)
    elif GRID_OPEN_RE.search(html_src):
        # First run: inject immediately after the grid opening tag.
        new_html = GRID_OPEN_RE.sub(
            lambda m: m.group(1) + "\n" + cards_block,
            html_src, count=1,
        )
    else:
        print(f"  WARNING: no dentist-grid found in {path}")
        new_html = html_src

    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(new_html)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("Fetching all clinics from Supabase…")
    all_clinics = fetch_all_clinics()
    print(f"  {len(all_clinics)} clinics loaded")

    # Group by region
    by_region: dict[str, list] = {}
    for c in all_clinics:
        by_region.setdefault(c.get("region", ""), []).append(c)

    # Fetch pricing for all clinic ids in one pass
    print("Fetching pricing…")
    all_ids = [c["id"] for c in all_clinics]
    pricing_map = fetch_pricing_for_ids(all_ids)
    print(f"  Pricing loaded for {len(pricing_map)} clinics")

    for filename, page_cfg in PAGES.items():
        if page_cfg is None:
            continue  # home page — no clinic grid
        region, suburb_filter_key = page_cfg

        region_clinics = by_region.get(region, [])
        if not region_clinics:
            print(f"  WARNING: no clinics found for region '{region}' ({filename})")
            continue

        # Apply suburb filter if specified
        if suburb_filter_key:
            allowed = SUBURB_FILTERS.get(suburb_filter_key, set())
            filtered = [c for c in region_clinics if (c.get("suburb_town") or c.get("town") or "") in allowed]
        else:
            filtered = region_clinics

        path = os.path.join(DOCS, filename)
        inject_page(path, filtered, pricing_map, region)
        print(f"  {filename}: {len(filtered)} clinics pre-rendered")

    print("\nDone. Run 'git diff --stat docs/' to review changes before pushing.")


if __name__ == "__main__":
    main()
