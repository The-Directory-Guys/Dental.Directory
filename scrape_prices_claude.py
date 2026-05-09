"""
Claude-powered price scraper for dental clinics.

Fetches each clinic's website, asks Claude Haiku to extract prices into a
fixed JSON schema (matching our standard treatment taxonomy), then uploads
directly to scraped_prices — no post-hoc normalisation needed.

Includes outlier detection: flags prices outside expected NZD ranges.

Usage:
    python scrape_prices_claude.py                   # preview, 10 clinics
    python scrape_prices_claude.py --apply           # apply all
    python scrape_prices_claude.py --limit 20        # limit to N clinics
    python scrape_prices_claude.py --id 123 --apply  # single clinic
    python scrape_prices_claude.py --validate-only   # check existing outliers
"""

import json
import os
import re
import sys
import time
import requests
import anthropic
from bs4 import BeautifulSoup
from datetime import date
from urllib.parse import urlparse
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_SERVICE_KEY"]
ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]
TODAY = str(date.today())

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=minimal",
}

FETCH_HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; DentalDirectoryBot/1.0)",
}

TIMEOUT = 12
MAX_TEXT_CHARS = 20000   # total chars across all pages sent to Claude
MAX_PAGES = 8            # max subpages to fetch per clinic (inc. homepage)

# URL path keywords that suggest a page has pricing info (checked case-insensitively)
PRICE_URL_KEYWORDS = {
    "price", "prices", "pricing", "fee", "fees", "cost", "costs",
    "payment", "payments", "finance", "treatment", "treatments",
    "service", "services", "offer", "offers", "special", "specials",
    "rate", "rates", "tariff", "schedule",
}

# ---------------------------------------------------------------------------
# Standard treatment list — these are the exact treatment names written to
# scraped_prices.treatment.  Claude fills them in from the page text.
# ---------------------------------------------------------------------------

TREATMENTS = [
    # Exam / consultation
    "Exam / checkup",
    "Consultation",
    "New patient offer",
    # Hygiene
    "Scale and polish",
    "Periodontal treatment",
    # Fillings
    "Filling",
    "Filling - composite",
    "Filling - amalgam",
    "Filling - glass ionomer",
    # Extractions
    "Extraction",
    "Extraction - simple",
    "Extraction - surgical",
    "Extraction - wisdom tooth",
    # Root canals
    "Root canal",
    "Root canal - front tooth",
    "Root canal - premolar",
    "Root canal - molar",
    # Crowns
    "Crown",
    "Crown - ceramic",
    "Crown - gold",
    # Veneers
    "Veneer",
    "Veneer - composite",
    "Veneer - porcelain",
    # Whitening
    "Whitening",
    "Whitening - in-chair",
    "Whitening - take-home",
    # Implants
    "Implant",
    "Implant - All-on-4",
    # Dentures
    "Denture",
    "Denture - full",
    "Denture - partial",
    "Denture repair",
    # Orthodontics
    "Orthodontics",
    "Orthodontics - aligners",
    "Orthodontics - braces",
    # X-rays
    "X-ray",
    "X-ray - OPG",
    "X-ray - intraoral",
    # Periodontal surgery
    "Bone graft",
    "Gum graft",
    "Crown lengthening",
    "Flap surgery",
    # Other clinical
    "Fissure sealant",
    "Fluoride",
    "Night guard",
    "Mouthguard",
    "IV sedation",
    "Botox / aesthetics",
    "Tooth gem",
    "Children's dentistry",
    # Payment options
    "Afterpay",
    "Q Card",
    "Zip",
    "Laybuy",
    "Gem Visa",
    "Farmers Card",
    "Finance Now",
    "MTF Finance",
    "Payment plan",
    "Credit card",
    # Insurance / government
    "ACC",
    "WINZ",
    "Southern Cross",
    "NIB",
    "Student discount",
    "Free teen dental care",
    "SuperGold Card",
    "Community Services Card",
]

# Payment/insurance fields — outlier check skips these
PAYMENT_FIELDS = {
    "Afterpay", "Q Card", "Zip", "Laybuy", "Gem Visa", "Farmers Card",
    "Finance Now", "MTF Finance", "Payment plan", "Credit card",
    "ACC", "WINZ", "Southern Cross", "NIB", "Student discount",
    "Free teen dental care", "SuperGold Card", "Community Services Card",
}

# ---------------------------------------------------------------------------
# Outlier bands (min_nzd, max_nzd) based on known NZ market rates
# ---------------------------------------------------------------------------

PRICE_BANDS = {
    "Exam / checkup":            (40,   350),
    "Consultation":              (40,   400),
    "New patient offer":         (20,   350),
    "Scale and polish":          (50,   600),
    "Periodontal treatment":     (100, 2500),
    "Filling":                   (80,  1000),
    "Filling - composite":       (80,  1000),
    "Filling - amalgam":         (80,   600),
    "Filling - glass ionomer":   (80,   600),
    "Extraction":                (80,   900),
    "Extraction - simple":       (80,   700),
    "Extraction - surgical":     (150, 1500),
    "Extraction - wisdom tooth": (150, 2500),
    "Root canal":                (400, 4000),
    "Root canal - front tooth":  (400, 2200),
    "Root canal - premolar":     (500, 2500),
    "Root canal - molar":        (600, 3500),
    "Crown":                     (800, 4500),
    "Crown - ceramic":           (1000, 4500),
    "Crown - gold":              (1000, 4500),
    "Veneer":                    (200, 4500),
    "Veneer - composite":        (200, 2000),
    "Veneer - porcelain":        (800, 4500),
    "Whitening":                 (150, 2000),
    "Whitening - in-chair":      (150, 2000),
    "Whitening - take-home":     (80,  1000),
    "Implant":                   (2000, 12000),
    "Implant - All-on-4":        (10000, 60000),
    "Denture - full":            (500, 5000),
    "Denture - partial":         (300, 4000),
    "Denture repair":            (50,   600),
    "Orthodontics - aligners":   (2000, 15000),
    "Orthodontics - braces":     (3000, 12000),
    "X-ray - OPG":               (50,   350),
    "X-ray - intraoral":         (20,   200),
    "Night guard":               (150, 1500),
    "Mouthguard":                (100, 1000),
    "Bone graft":                (500, 6000),
    "Gum graft":                 (500, 6000),
    "Crown lengthening":         (200, 3000),
    "IV sedation":               (200, 2500),
    "Fissure sealant":           (30,   250),
    "Fluoride":                  (15,   120),
    "Tooth gem":                 (30,   500),
    "Botox / aesthetics":        (50,   800),
}


def safe(s: str) -> str:
    return s.encode("ascii", "replace").decode()


def domain(url: str) -> str:
    try:
        return urlparse(url).netloc.lstrip("www.") or url
    except Exception:
        return url


def _fetch_soup(url: str):
    """Fetch a URL and return (final_url, BeautifulSoup) or (None, None) on failure."""
    try:
        r = requests.get(url, headers=FETCH_HEADERS, timeout=TIMEOUT, allow_redirects=True)
        if r.status_code != 200:
            return None, None
        return r.url, BeautifulSoup(r.text, "html.parser")
    except Exception:
        return None, None


def _soup_to_text(soup) -> str:
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    return soup.get_text(" ", strip=True)


def _score_url(path: str) -> int:
    """Higher score = more likely to contain pricing info."""
    path_lower = path.lower()
    return sum(1 for kw in PRICE_URL_KEYWORDS if kw in path_lower)


def get_site_text(url: str) -> str | None:
    """
    Fetch homepage + prioritised subpages, return combined text for Claude.
    Links are extracted from the homepage only; only same-domain links are
    followed. Price-related URLs are fetched first.
    """
    from urllib.parse import urljoin

    base_domain = urlparse(url).netloc
    visited = set()
    pages = []  # list of (page_url, text)

    # --- Homepage ---
    final_url, soup = _fetch_soup(url)
    if soup is None:
        return None
    visited.add(final_url or url)
    pages.append((final_url or url, _soup_to_text(soup)))

    # --- Collect internal links from homepage ---
    candidates = []
    for a in soup.find_all("a", href=True):
        href = urljoin(url, a["href"]).split("#")[0].split("?")[0]
        parsed = urlparse(href)
        if parsed.netloc != base_domain:
            continue
        if href in visited:
            continue
        if parsed.path.lower().endswith((".pdf", ".jpg", ".png", ".jpeg", ".gif")):
            continue
        score = _score_url(parsed.path)
        candidates.append((score, href))

    # Sort: price-related URLs first, then alphabetically for stability
    candidates.sort(key=lambda x: (-x[0], x[1]))
    seen_hrefs = set()
    queue = []
    for score, href in candidates:
        if href not in seen_hrefs:
            seen_hrefs.add(href)
            queue.append(href)

    # --- Fetch subpages up to MAX_PAGES total ---
    for href in queue:
        if len(pages) >= MAX_PAGES:
            break
        if href in visited:
            continue
        visited.add(href)
        _, sub_soup = _fetch_soup(href)
        if sub_soup is None:
            continue
        pages.append((href, _soup_to_text(sub_soup)))
        time.sleep(0.3)

    # --- Combine, label each page, truncate to MAX_TEXT_CHARS ---
    parts = []
    total = 0
    for page_url, text in pages:
        header = f"[Page: {page_url}]\n"
        available = MAX_TEXT_CHARS - total - len(header)
        if available <= 100:
            break
        chunk = text[:available]
        parts.append(header + chunk)
        total += len(header) + len(chunk)

    return "\n\n".join(parts) if parts else None


def ask_claude(clinic_name: str, url: str, text: str) -> dict | None:
    schema_obj = {t: None for t in TREATMENTS}
    schema_obj["other"] = []

    prompt = f"""Extract dental pricing and payment information from this website. Only include information explicitly stated on the page — do not infer, estimate, or fabricate anything.

Clinic: {clinic_name}
URL: {url}

Page text:
{text[:MAX_TEXT_CHARS]}

Fill in the JSON schema below. Rules:
- For price fields: use the exact price text from the page (e.g. "$120", "from $165", "$200-$350"). Set to null if not mentioned on the page.
- Use the most specific field available. If the page says "composite filling $250", use "Filling - composite" not "Filling". Only use a generic field when no specific type is stated.
- For payment/insurance fields (Afterpay, Q Card, ACC, WINZ, etc.): describe the terms briefly (e.g. "4 fortnightly payments", "12 months interest-free", "Available", "Registered provider"). Set to null if not mentioned.
- "other": list any priced items not covered by the schema as {{"treatment": "...", "price": "..."}}.

{json.dumps(schema_obj, indent=2)}

Return ONLY valid JSON, no explanation or markdown."""

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    try:
        msg = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = msg.content[0].text.strip()
        raw = re.sub(r"^```(?:json)?\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)
        return json.loads(raw)
    except Exception as e:
        print(f"    Claude error: {e}")
        return None


def build_rows(clinic_id: int, url: str, data: dict) -> list[dict]:
    src = f"scraper:{domain(url)}"
    rows = []

    for treatment in TREATMENTS:
        val = data.get(treatment)
        if not val:
            continue
        rows.append({
            "clinic_id":   clinic_id,
            "source":      src,
            "treatment":   treatment,
            "price_nzd":   None,
            "price_label": str(val).strip(),
            "source_url":  url,
            "notes":       None,
        })

    for item in (data.get("other") or []):
        if not isinstance(item, dict):
            continue
        t = str(item.get("treatment") or "").strip()
        p = str(item.get("price") or "").strip()
        if t and p:
            rows.append({
                "clinic_id":   clinic_id,
                "source":      src,
                "treatment":   t,
                "price_nzd":   None,
                "price_label": p,
                "source_url":  url,
                "notes":       None,
            })

    return rows


def parse_price(label: str) -> float | None:
    """Extract the first dollar amount from a price label."""
    m = re.search(r"\$\s*(\d[\d,]*(?:\.\d+)?)", label)
    if m:
        return float(m.group(1).replace(",", ""))
    return None


def check_outliers(rows: list[dict]) -> list[dict]:
    """Return rows whose first parsed price falls outside PRICE_BANDS."""
    flagged = []
    for row in rows:
        if row.get("treatment") in PAYMENT_FIELDS:
            continue
        band = PRICE_BANDS.get(row["treatment"])
        if not band:
            continue
        price = parse_price(row.get("price_label") or "")
        if price is None:
            continue
        lo, hi = band
        if price < lo or price > hi:
            flagged.append({**row, "_parsed": price, "_band": band})
    return flagged


# ---------------------------------------------------------------------------
# Supabase helpers
# ---------------------------------------------------------------------------

def fetch_clinics(clinic_id: int | None = None, region: str | None = None) -> list[dict]:
    rows = []
    page_size = 1000
    offset = 0
    id_filter = f"&id=eq.{clinic_id}" if clinic_id else ""
    region_filter = f"&region=ilike.*{region}*" if region else ""
    while True:
        url = (
            f"{SUPABASE_URL}/rest/v1/dental_clinics"
            f"?select=id,name,website"
            f"&website=not.is.null&website=neq."
            f"{id_filter}{region_filter}"
            f"&order=id.asc"
            f"&limit={page_size}&offset={offset}"
        )
        r = requests.get(url, headers=HEADERS, timeout=15)
        r.raise_for_status()
        batch = r.json()
        rows.extend(batch)
        if len(batch) < page_size:
            break
        offset += page_size
    return rows


def fetch_manual_clinic_ids() -> set:
    resp = requests.get(
        f"{SUPABASE_URL}/rest/v1/scraped_prices"
        f"?select=clinic_id&source=like.manual:*&limit=10000",
        headers=HEADERS, timeout=15,
    )
    resp.raise_for_status()
    return {r["clinic_id"] for r in resp.json()}


def delete_scraper_rows(clinic_id: int):
    for source_filter in ["source=like.scraper:*", "source=like.region_website_scrape:*"]:
        resp = requests.delete(
            f"{SUPABASE_URL}/rest/v1/scraped_prices"
            f"?clinic_id=eq.{clinic_id}&{source_filter}",
            headers=HEADERS, timeout=15,
        )
        resp.raise_for_status()


def insert_rows(rows: list[dict]):
    resp = requests.post(
        f"{SUPABASE_URL}/rest/v1/scraped_prices",
        headers=HEADERS, json=rows, timeout=15,
    )
    resp.raise_for_status()


def tag_scrape_error(clinic_id: int, url: str, reason: str):
    """Insert a sentinel row so failed scrapes are visible in the DB."""
    delete_scraper_rows(clinic_id)
    row = {
        "clinic_id": clinic_id,
        "source": "scraper:error",
        "treatment": "Scrape error",
        "price_label": reason,
        "source_url": url or "",
    }
    resp = requests.post(
        f"{SUPABASE_URL}/rest/v1/scraped_prices",
        headers=HEADERS, json=row, timeout=15,
    )
    resp.raise_for_status()


def update_clinic_date(clinic_id: int):
    resp = requests.patch(
        f"{SUPABASE_URL}/rest/v1/dental_clinics?id=eq.{clinic_id}",
        headers=HEADERS, json={"prices_last_updated": TODAY}, timeout=15,
    )
    resp.raise_for_status()


# ---------------------------------------------------------------------------
# Main runs
# ---------------------------------------------------------------------------

def run(apply: bool, limit: int | None, clinic_id: int | None, region: str | None = None):
    label = f"Claude price scraper ({'APPLY' if apply else 'PREVIEW'})"
    if region:
        label += f" — region: {region}"
    print(label)

    clinics = fetch_clinics(clinic_id, region)

    if not apply and limit is None and clinic_id is None:
        print("Preview mode: showing first 10 clinics. Use --apply to run all.")
        clinics = clinics[:10]
    elif limit:
        clinics = clinics[:limit]

    print("Fetching manually verified clinic IDs...")
    manual_ids = fetch_manual_clinic_ids()
    to_scan = [c for c in clinics if c["id"] not in manual_ids]
    print(f"  {len(clinics)} clinics, {len(manual_ids)} already manual -> {len(to_scan)} to scan\n")

    total_items = 0
    total_outliers = 0
    errors = 0

    for i, clinic in enumerate(to_scan, 1):
        cid = clinic["id"]
        name = safe(clinic["name"])
        url = clinic["website"]

        text = get_site_text(url)
        if text is None:
            print(f"  [{i:4d}/{len(to_scan)}] ERR  {name}")
            errors += 1
            if apply:
                try:
                    tag_scrape_error(cid, url, "Website could not be fetched")
                    update_clinic_date(cid)
                except Exception as e:
                    print(f"    DB error tagging: {e}")
            continue

        data = ask_claude(clinic["name"], url, text)
        if data is None:
            print(f"  [{i:4d}/{len(to_scan)}] ERR  {name} (Claude failed)")
            errors += 1
            if apply:
                try:
                    tag_scrape_error(cid, url, "Claude API error")
                    update_clinic_date(cid)
                except Exception as e:
                    print(f"    DB error tagging: {e}")
            continue

        rows = build_rows(cid, url, data)
        outliers = check_outliers(rows)

        n_items = len(rows)
        flag = " [!]" if outliers else ""
        print(f"  [{i:4d}/{len(to_scan)}] {name} -- {n_items} items{flag}")

        for o in outliers:
            print(f"    OUTLIER: {o['treatment']}: {o['price_label']}"
                  f" (${o['_parsed']:.0f}, expected ${o['_band'][0]}-${o['_band'][1]})")

        total_items += n_items
        total_outliers += len(outliers)

        if apply:
            try:
                delete_scraper_rows(cid)
                if rows:
                    insert_rows(rows)
                update_clinic_date(cid)
            except Exception as e:
                print(f"    DB error: {e}")
                errors += 1

        time.sleep(0.5)

    print(f"\n{'='*60}")
    print(f"Scanned: {len(to_scan)}, Items extracted: {total_items}, "
          f"Outliers: {total_outliers}, Errors: {errors}")
    if not apply:
        print("Run with --apply to write to Supabase.")


def validate_only():
    """Check outliers across all existing scraper:* rows in the DB."""
    print("Fetching all scraper:* rows for outlier check...")
    rows = []
    page_size = 1000
    offset = 0
    while True:
        url = (
            f"{SUPABASE_URL}/rest/v1/scraped_prices"
            f"?select=id,clinic_id,treatment,price_label,source_url"
            f"&source=like.scraper:*"
            f"&order=id.asc"
            f"&limit={page_size}&offset={offset}"
        )
        r = requests.get(url, headers=HEADERS, timeout=15)
        r.raise_for_status()
        batch = r.json()
        rows.extend(batch)
        if len(batch) < page_size:
            break
        offset += page_size

    print(f"  {len(rows)} rows fetched")
    outliers = check_outliers(rows)
    print(f"  {len(outliers)} outliers flagged\n")

    by_treatment = {}
    for o in outliers:
        by_treatment.setdefault(o["treatment"], []).append(o)

    for treatment in sorted(by_treatment):
        print(f"  {treatment}:")
        for o in by_treatment[treatment]:
            print(f"    clinic_id={o['clinic_id']}  {o['price_label']}"
                  f"  (${o['_parsed']:.0f}, expected ${o['_band'][0]}-${o['_band'][1]})")
            print(f"    {o['source_url']}")


# ---------------------------------------------------------------------------

if __name__ == "__main__":
    args = sys.argv[1:]
    if "--validate-only" in args:
        validate_only()
    else:
        apply = "--apply" in args
        limit = None
        cli_id = None
        region = None
        for j, a in enumerate(args):
            if a == "--limit" and j + 1 < len(args):
                limit = int(args[j + 1])
            if a == "--id" and j + 1 < len(args):
                cli_id = int(args[j + 1])
            if a == "--region" and j + 1 < len(args):
                region = args[j + 1]
        run(apply, limit, cli_id, region)
