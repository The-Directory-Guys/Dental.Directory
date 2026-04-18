"""
Dental Clinic Pricing Scraper
Fetches clinic websites and uses Claude AI to extract pricing information.
Crawls multiple pages per site (homepage + pricing/fees/services subpages).
Uses requests for simple sites, falls back to Playwright for JS-heavy sites.

Usage:
    pip install anthropic requests beautifulsoup4 playwright
    playwright install chromium

    # Scrape specific regions from Supabase:
    python dental-price-scraper.py --regions Auckland "Bay of Plenty"

    # Scrape from a CSV file:
    python dental-price-scraper.py --input my_clinics.csv --output results.csv

    python dental-price-scraper.py --no-playwright   # skip Playwright fallback
    python dental-price-scraper.py --max-pages 5     # crawl up to 5 subpages
"""

import anthropic
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import csv
import time
import json
import argparse
import logging
import os
import re
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]
DEFAULT_INPUT     = "nz_dental_clinics.csv"
DEFAULT_OUTPUT    = "dental_clinics_with_pricing.csv"

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_SERVICE_KEY"]

# Max subpages to crawl per clinic (homepage is always crawled, then up to this many subpages)
DEFAULT_MAX_SUBPAGES = 3

# How long to wait between requests (seconds) — be polite to clinic servers
REQUEST_DELAY = 1.0

# Max characters of combined page text to send to Claude (keeps costs low)
MAX_PAGE_CHARS = 12000

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}

PRICING_FIELDS = [
    "checkup",
    "scale_and_polish",
    "filling",
    "extraction",
    "whitening",
    "new_patient",
    "other",
    "has_pricing",
    "pages_crawled",
]

# Keywords that suggest a page likely contains pricing info
# Scored by relevance — higher score = crawl first
PRICING_PAGE_KEYWORDS = [
    (10, r"\bfee[s]?\b"),
    (10, r"\bpric(e|es|ing)\b"),
    (9,  r"\bcost[s]?\b"),
    (8,  r"\brates?\b"),
    (7,  r"\bservice[s]?\b"),
    (6,  r"\btreatment[s]?\b"),
    (5,  r"\bwhat.we.offer\b"),
    (4,  r"\babout\b"),
    (3,  r"\bnew.patient[s]?\b"),
]


# ---------------------------------------------------------------------------
# Supabase helpers
# ---------------------------------------------------------------------------

NZ_REGIONS = [
    "Auckland", "Bay of Plenty", "Canterbury", "Gisborne", "Hawke's Bay",
    "Manawatū-Whanganui", "Marlborough", "Nelson", "Northland", "Otago",
    "Southland", "Taranaki", "Waikato", "Wellington", "West Coast",
]


def fetch_all_regions() -> list[str]:
    """Return all NZ dental regions."""
    log.info(f"Using {len(NZ_REGIONS)} regions: {', '.join(NZ_REGIONS)}")
    return NZ_REGIONS


def fetch_clinics_from_supabase(regions: list[str]) -> list[dict]:
    """
    Fetch dental clinics from Supabase for the given regions.
    Only returns clinics that have a website and no verified prices yet.
    """
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
    }

    all_clinics = []
    for region in regions:
        url = (
            f"{SUPABASE_URL}/rest/v1/dental_clinics"
            f"?select=id,name,website,region,suburb_town"
            f"&region=eq.{requests.utils.quote(region)}"
            f"&website=neq."
            f"&prices_last_updated=is.null"
            f"&order=name.asc"
        )
        resp = requests.get(url, headers=headers, timeout=15)
        resp.raise_for_status()
        rows = resp.json()
        log.info(f"Fetched {len(rows)} clinics for region '{region}'")
        for row in rows:
            all_clinics.append({
                "place_id":    str(row["id"]),
                "name":        row.get("name", ""),
                "website":     row.get("website", ""),
                "region":      row.get("region", ""),
                "suburb_town": row.get("suburb_town", ""),
            })

    return all_clinics


# ---------------------------------------------------------------------------
# URL utilities
# ---------------------------------------------------------------------------

def normalise_url(url: str) -> str:
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    return url.rstrip("/")


def same_domain(url1: str, url2: str) -> bool:
    return urlparse(url1).netloc == urlparse(url2).netloc


def score_url_for_pricing(url: str) -> int:
    """Return a relevance score for how likely a URL leads to pricing content."""
    path = urlparse(url).path.lower()
    score = 0
    for weight, pattern in PRICING_PAGE_KEYWORDS:
        if re.search(pattern, path):
            score += weight
    return score


def find_pricing_subpages(base_url: str, html: str, max_pages: int) -> list[str]:
    """
    Parse links from a page and return the most promising subpages
    for pricing content, sorted by relevance score.
    """
    soup = BeautifulSoup(html, "html.parser")
    seen = set()
    candidates = []

    for tag in soup.find_all("a", href=True):
        href = tag["href"].strip()
        if not href or href.startswith(("#", "mailto:", "tel:", "javascript:")):
            continue

        full_url = urljoin(base_url, href).rstrip("/")

        if not same_domain(base_url, full_url):
            continue
        if full_url == base_url:
            continue
        if full_url in seen:
            continue

        seen.add(full_url)
        score = score_url_for_pricing(full_url)
        if score > 0:
            candidates.append((score, full_url))

    candidates.sort(key=lambda x: x[0], reverse=True)
    return [url for _, url in candidates[:max_pages]]


# ---------------------------------------------------------------------------
# Page fetching
# ---------------------------------------------------------------------------

def fetch_with_requests(url: str) -> tuple[str | None, str | None]:
    """Fast fetch. Returns (cleaned_text, raw_html)."""
    try:
        response = requests.get(url, timeout=10, headers=HEADERS)
        response.raise_for_status()
        raw_html = response.text
        soup = BeautifulSoup(raw_html, "html.parser")
        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()
        text = soup.get_text(separator=" ", strip=True)
        return (text if text else None), raw_html
    except Exception as e:
        log.debug(f"requests failed for {url}: {e}")
        return None, None


def fetch_with_playwright(url: str) -> tuple[str | None, str | None]:
    """Playwright fallback for JS-rendered sites. Returns (cleaned_text, raw_html)."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        log.warning("Playwright not installed. Run: pip install playwright && playwright install chromium")
        return None, None

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(extra_http_headers=HEADERS)
            page.goto(url, timeout=15000, wait_until="domcontentloaded")
            page.wait_for_timeout(2000)
            raw_html = page.content()
            browser.close()

        soup = BeautifulSoup(raw_html, "html.parser")
        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()
        text = soup.get_text(separator=" ", strip=True)
        return (text if text else None), raw_html

    except Exception as e:
        log.debug(f"Playwright failed for {url}: {e}")
        return None, None


def fetch_page(url: str, use_playwright: bool = True) -> tuple[str | None, str | None, str]:
    """
    Fetch a page with requests, falling back to Playwright if content is thin.
    Returns (cleaned_text, raw_html, method_used).
    """
    url = normalise_url(url)
    text, html = fetch_with_requests(url)

    if use_playwright and (text is None or len(text) < 200):
        log.debug(f"  Falling back to Playwright for {url}")
        text, html = fetch_with_playwright(url)
        if text:
            return text, html, "playwright"
        return None, None, "failed"

    if text:
        return text, html, "requests"
    return None, None, "failed"


# ---------------------------------------------------------------------------
# Multi-page crawler
# ---------------------------------------------------------------------------

def crawl_clinic_site(
    base_url: str,
    use_playwright: bool = True,
    max_subpages: int = DEFAULT_MAX_SUBPAGES,
) -> tuple[str, list[str], str]:
    """
    Crawl a clinic's website: homepage plus up to max_subpages pricing-relevant subpages.
    Subpages are discovered from links on the homepage and scored by how likely they
    are to contain pricing (e.g. /fees, /pricing, /services score highest).

    Returns:
        combined_text  — all page text joined for Claude
        pages_visited  — list of URLs actually fetched
        method         — fetch method used
    """
    base_url = normalise_url(base_url)
    pages_visited = []
    all_text_parts = []
    method = "failed"

    # --- Fetch homepage ---
    log.info(f"  Homepage: {base_url}")
    text, html, method = fetch_page(base_url, use_playwright=use_playwright)

    if not text:
        return "", [], "failed"

    all_text_parts.append(f"[PAGE: {base_url}]\n{text}")
    pages_visited.append(base_url)
    time.sleep(REQUEST_DELAY)

    # --- Discover and fetch subpages ---
    if html and max_subpages > 0:
        subpages = find_pricing_subpages(base_url, html, max_pages=max_subpages)

        if subpages:
            log.info(f"  Found {len(subpages)} pricing subpage(s): {', '.join(urlparse(u).path for u in subpages)}")

        for subpage_url in subpages:
            log.info(f"  Subpage: {subpage_url}")
            sub_text, _, sub_method = fetch_page(subpage_url, use_playwright=use_playwright)

            if sub_text:
                all_text_parts.append(f"[PAGE: {subpage_url}]\n{sub_text}")
                pages_visited.append(subpage_url)
                if sub_method == "playwright":
                    method = "playwright"
            else:
                log.info(f"  Could not fetch subpage")

            time.sleep(REQUEST_DELAY)

    combined = "\n\n".join(all_text_parts)
    return combined[:MAX_PAGE_CHARS], pages_visited, method


# ---------------------------------------------------------------------------
# AI pricing extraction
# ---------------------------------------------------------------------------

def extract_pricing(pages_text: str, pages_visited: list[str], client: anthropic.Anthropic) -> dict:
    """Send combined page content to Claude and extract structured pricing data."""

    pages_list = "\n".join(f"- {p}" for p in pages_visited)

    prompt = f"""You are extracting dental pricing information from a clinic website.

Pages crawled:
{pages_list}

Combined page content:
{pages_text}

Extract any pricing information you can find across all pages. Look for:
- Checkup / exam fees
- Scale and polish / clean fees
- Filling fees (tooth-coloured or amalgam)
- Extraction fees
- Teeth whitening fees
- New patient consultation fees
- Any other specific prices mentioned

Return ONLY a JSON object with these exact fields (use null if not found):
{{
    "checkup": "price or range as string e.g. '$95' or '$85-$110'",
    "scale_and_polish": "price or range as string",
    "filling": "price or range as string",
    "extraction": "price or range as string",
    "whitening": "price or range as string",
    "new_patient": "price or range as string",
    "other": "any other pricing info found, as a brief string",
    "has_pricing": true or false
}}

Return ONLY valid JSON. No explanation, no markdown, no backticks."""

    try:
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=500,
            messages=[{"role": "user", "content": prompt}]
        )
        raw = response.content[0].text.strip()
        raw = raw.replace("```json", "").replace("```", "").strip()
        pricing = json.loads(raw)

        for field in PRICING_FIELDS:
            pricing.setdefault(field, None)

        return pricing

    except json.JSONDecodeError as e:
        log.warning(f"JSON parse error: {e}")
        return {field: None for field in PRICING_FIELDS}
    except Exception as e:
        log.warning(f"Claude API error: {e}")
        return {field: None for field in PRICING_FIELDS}


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------

def process_clinics(
    input_csv: str | None,
    output_csv: str,
    use_playwright: bool = True,
    max_subpages: int = DEFAULT_MAX_SUBPAGES,
    resume: bool = True,
    clinics: list[dict] | None = None,
):
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    if clinics is None:
        with open(input_csv, newline="", encoding="utf-8") as f:
            clinics = list(csv.DictReader(f))
        log.info(f"Loaded {len(clinics)} clinics from {input_csv}")
    else:
        log.info(f"Processing {len(clinics)} clinics from Supabase")

    already_done = set()
    if resume:
        # Check the output file itself
        if Path(output_csv).exists():
            with open(output_csv, newline="", encoding="utf-8") as f:
                for row in csv.DictReader(f):
                    already_done.add(row.get("place_id", ""))
        # Also check any other *_pricing.csv files so we don't re-scrape
        # clinics already processed in a previous run with a different output file
        for other_csv in Path(".").glob("*_pricing.csv"):
            if str(other_csv) == output_csv:
                continue
            with open(other_csv, newline="", encoding="utf-8") as f:
                for row in csv.DictReader(f):
                    already_done.add(row.get("place_id", ""))
        log.info(f"Resuming — {len(already_done)} clinics already processed")

    sample_clinic = clinics[0] if clinics else {}
    extra_fields = ["scrape_status", "fetch_method"] + PRICING_FIELDS
    fieldnames = list(sample_clinic.keys()) + extra_fields

    mode = "a" if already_done else "w"
    with open(output_csv, mode, newline="", encoding="utf-8") as outfile:
        writer = csv.DictWriter(outfile, fieldnames=fieldnames, extrasaction="ignore")
        if not already_done:
            writer.writeheader()

        processed = skipped = no_url = pricing_found = 0

        for i, clinic in enumerate(clinics):
            place_id = clinic.get("place_id", "")
            name     = clinic.get("name", "Unknown")

            if place_id in already_done:
                skipped += 1
                continue

            url = clinic.get("website", "").strip()
            if not url:
                log.info(f"[{i+1}/{len(clinics)}] {name} — no website, skipping")
                row = {**clinic, "scrape_status": "no_url", "fetch_method": None}
                for field in PRICING_FIELDS:
                    row[field] = None
                writer.writerow(row)
                outfile.flush()
                no_url += 1
                continue

            log.info(f"[{i+1}/{len(clinics)}] {name} ({url})")

            combined_text, pages_visited, method = crawl_clinic_site(
                url,
                use_playwright=use_playwright,
                max_subpages=max_subpages,
            )

            if not combined_text:
                log.info(f"  Could not fetch any pages")
                row = {**clinic, "scrape_status": "fetch_failed", "fetch_method": method}
                for field in PRICING_FIELDS:
                    row[field] = None
                writer.writerow(row)
                outfile.flush()
                processed += 1
                continue

            log.info(f"  Crawled {len(pages_visited)} page(s), {len(combined_text)} chars total")

            pricing = extract_pricing(combined_text, pages_visited, client)
            pricing["pages_crawled"] = ", ".join(pages_visited)

            if pricing.get("has_pricing"):
                pricing_found += 1
                log.info(f"  ✓ Pricing found")
            else:
                log.info(f"  — No pricing found")

            row = {**clinic, "scrape_status": "success", "fetch_method": method, **pricing}
            writer.writerow(row)
            outfile.flush()
            processed += 1

    log.info(f"\n--- Summary ---")
    log.info(f"Processed:     {processed}")
    log.info(f"Skipped:       {skipped} (already done)")
    log.info(f"No URL:        {no_url}")
    log.info(f"Pricing found: {pricing_found}")
    log.info(f"Results saved to {output_csv}")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Scrape dental clinic websites for pricing using Claude AI")
    parser.add_argument("--input",         default=DEFAULT_INPUT,               help="Input CSV from dental_scraper.py")
    parser.add_argument("--output",        default=DEFAULT_OUTPUT,              help="Output CSV with pricing data")
    parser.add_argument("--regions",       nargs="+",                           help='Fetch clinics from Supabase for these regions, e.g. --regions Auckland "Bay of Plenty"')
    parser.add_argument("--all-regions",   action="store_true",                 help="Fetch unverified clinics from every region in Supabase")
    parser.add_argument("--no-playwright", action="store_true",                 help="Disable Playwright fallback")
    parser.add_argument("--no-resume",     action="store_true",                 help="Reprocess all clinics")
    parser.add_argument("--max-pages",     type=int, default=DEFAULT_MAX_SUBPAGES, help="Max subpages per clinic (default: 3)")
    parser.add_argument("--key",           default=None,                        help="Anthropic API key")
    args = parser.parse_args()

    if args.key:
        ANTHROPIC_API_KEY = args.key

    if args.all_regions or args.regions:
        regions = fetch_all_regions() if args.all_regions else args.regions
        clinics = fetch_clinics_from_supabase(regions)
        if args.all_regions:
            output_csv = args.output if args.output != DEFAULT_OUTPUT else "all_regions_pricing.csv"
        else:
            region_slug = "_".join(r.lower().replace(" ", "_") for r in args.regions)
            output_csv = args.output if args.output != DEFAULT_OUTPUT else f"{region_slug}_pricing.csv"
        process_clinics(
            input_csv=None,
            output_csv=output_csv,
            use_playwright=not args.no_playwright,
            max_subpages=args.max_pages,
            resume=not args.no_resume,
            clinics=clinics,
        )
    else:
        process_clinics(
            input_csv=args.input,
            output_csv=args.output,
            use_playwright=not args.no_playwright,
            max_subpages=args.max_pages,
            resume=not args.no_resume,
        )